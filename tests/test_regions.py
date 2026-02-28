"""Tests for regional pipeline processing."""

import numpy as np
import pandas as pd

from pipeline.config import AGE_COLUMNS, CANONICAL_CAUSES, REGION_MAP
from pipeline.ingest import aggregate_regional
from pipeline.compute import compute
from pipeline.anomalies import detect_anomalies


def _make_regional_df(region_codes=None, years=None, weeks=None, causes=None):
    """Build a synthetic regional DataFrame matching Parquet structure."""
    if region_codes is None:
        region_codes = list(REGION_MAP.keys())
    if years is None:
        years = [2017, 2018, 2019, 2022, 2023, 2024, 2025]
    if weeks is None:
        weeks = list(range(1, 53))
    if causes is None:
        causes = CANONICAL_CAUSES

    rows = []
    rng = np.random.default_rng(42)
    for rc in region_codes:
        for y in years:
            for w in weeks:
                for c in causes:
                    base = rng.integers(10, 200)
                    row = {
                        "RegionCodigo": rc,
                        "Anio": y,
                        "SE": w,
                        "Causa": c,
                        "NumTotal": base,
                    }
                    for age_col in AGE_COLUMNS:
                        row[age_col] = rng.integers(1, base // 5 + 2)
                    rows.append(row)

    return pd.DataFrame(rows)


class TestAggregateRegional:
    def test_grouping_columns(self):
        df = _make_regional_df(region_codes=[1, 13], years=[2024], weeks=[1, 2])
        result = aggregate_regional(df)
        assert "RegionCodigo" in result.columns
        assert "Anio" in result.columns
        assert "SE" in result.columns
        assert "Causa" in result.columns

    def test_aggregation_sums(self):
        """Two rows for same (region, year, week, cause) should sum."""
        df = pd.DataFrame([
            {"RegionCodigo": 1, "Anio": 2024, "SE": 1, "Causa": "Total", "NumTotal": 50},
            {"RegionCodigo": 1, "Anio": 2024, "SE": 1, "Causa": "Total", "NumTotal": 30},
        ])
        result = aggregate_regional(df)
        assert len(result) == 1
        assert result.iloc[0]["NumTotal"] == 80

    def test_drops_null_region(self):
        df = pd.DataFrame([
            {"RegionCodigo": 1, "Anio": 2024, "SE": 1, "Causa": "Total", "NumTotal": 50},
            {"RegionCodigo": None, "Anio": 2024, "SE": 1, "Causa": "Total", "NumTotal": 30},
        ])
        result = aggregate_regional(df)
        assert len(result) == 1
        assert result.iloc[0]["RegionCodigo"] == 1

    def test_shape_matches_expected_columns(self):
        df = _make_regional_df(region_codes=[13], years=[2024], weeks=[1])
        result = aggregate_regional(df)
        expected_cols = {"RegionCodigo", "Anio", "SE", "Causa", "NumTotal"}
        expected_cols.update(AGE_COLUMNS.keys())
        assert set(result.columns) == expected_cols


class TestRegionalCompute:
    def test_output_keys_match_national(self):
        """Regional compute should produce same JSON structure as national."""
        df = _make_regional_df(region_codes=[13])
        regional = aggregate_regional(df)
        region_df = regional[regional["RegionCodigo"] == 13].drop(columns=["RegionCodigo"])

        baselines_json, alert_json, _ = compute(region_df)
        anomalies_json, alert_json = detect_anomalies(region_df, alert_json)

        # Same top-level keys as national
        assert "reference_years" in baselines_json
        assert "weeks" in baselines_json
        assert "current" in alert_json
        assert "timeseries" in alert_json
        assert "total_anomalies" in anomalies_json
        assert "events" in anomalies_json

    def test_timeseries_has_entries(self):
        df = _make_regional_df(region_codes=[13])
        regional = aggregate_regional(df)
        region_df = regional[regional["RegionCodigo"] == 13].drop(columns=["RegionCodigo"])

        _, alert_json, _ = compute(region_df)
        assert len(alert_json["timeseries"]) > 0
        entry = alert_json["timeseries"][0]
        assert "year" in entry
        assert "week" in entry
        assert "color" in entry
        assert "by_cause" in entry


class TestRegionIndex:
    def test_completeness(self):
        """All 16 regions should produce index entries when data exists."""
        df = _make_regional_df()
        regional = aggregate_regional(df)
        entries = []
        for code, name in sorted(REGION_MAP.items()):
            region_df = regional[regional["RegionCodigo"] == code].drop(columns=["RegionCodigo"])
            if region_df.empty:
                continue
            _, alert_json, _ = compute(region_df)
            current = alert_json.get("current")
            entries.append({
                "code": code,
                "name": name,
                "color": current["color"] if current else "no_data",
            })
        assert len(entries) == 16


class TestEmptyRegion:
    def test_empty_region_skipped(self):
        """A region with no data should be gracefully skipped."""
        df = _make_regional_df(region_codes=[1])
        regional = aggregate_regional(df)
        # Filter to a code that doesn't exist
        region_df = regional[regional["RegionCodigo"] == 99].drop(columns=["RegionCodigo"])
        assert region_df.empty
