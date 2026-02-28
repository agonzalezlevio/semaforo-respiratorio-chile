"""Tests for pipeline/forecast.py"""

import numpy as np
import pandas as pd
import pytest

from pipeline.forecast import (
    build_ratio_series,
    build_features,
    get_feature_columns,
    estimate_exceedance_prob,
    _next_week,
    HAS_LGB,
)
from pipeline.compute import classify_color


def _make_national(n_years=5, weeks_per_year=52):
    """Builds a synthetic national DataFrame (avoids 2020-2021 excluded years)."""
    rows = []
    for year in range(2015, 2015 + n_years):
        for se in range(1, weeks_per_year + 1):
            base = 40000 + 5000 * np.sin(2 * np.pi * se / 52)
            noise = np.random.RandomState(year * 100 + se).normal(0, 1000)
            total = max(int(base + noise), 1000)
            rows.append({"Anio": year, "SE": se, "Causa": "Total", "NumTotal": total})
    return pd.DataFrame(rows)


def _make_baselines(weeks=52):
    """Builds a synthetic baselines DataFrame matching compute_baselines output."""
    rows = []
    for se in range(1, weeks + 1):
        median = 40000 + 5000 * np.sin(2 * np.pi * se / 52)
        rows.append({
            "SE": se,
            "Causa": "Total",
            "NumTotal_median": median,
            "NumTotal_p25": median * 0.9,
            "NumTotal_p75": median * 1.1,
            "NumTotal_p90": median * 1.2,
        })
    return pd.DataFrame(rows)


class TestBuildRatioSeries:
    def test_returns_expected_columns(self):
        national = _make_national()
        baselines_df = _make_baselines()
        result = build_ratio_series(national, baselines_df)
        for col in ["Anio", "SE", "NumTotal", "baseline_median", "ratio", "ratio_t"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_ratio_computation(self):
        national = _make_national()
        baselines_df = _make_baselines()
        result = build_ratio_series(national, baselines_df)
        for _, row in result.head(5).iterrows():
            expected = row["NumTotal"] / row["baseline_median"]
            assert abs(row["ratio"] - expected) < 0.001

    def test_log_transform(self):
        national = _make_national()
        baselines_df = _make_baselines()
        result = build_ratio_series(national, baselines_df)
        for _, row in result.head(5).iterrows():
            expected = np.log(row["ratio"])
            assert abs(row["ratio_t"] - expected) < 0.001

    def test_se53_maps_to_se1(self):
        """SE 53 should use SE 1 baseline."""
        national = pd.DataFrame([
            {"Anio": 2024, "SE": 53, "Causa": "Total", "NumTotal": 30000},
            {"Anio": 2024, "SE": 1, "Causa": "Total", "NumTotal": 35000},
        ])
        baselines_df = _make_baselines()
        result = build_ratio_series(national, baselines_df)
        se53_row = result[result["SE"] == 53]
        se1_row = result[result["SE"] == 1]
        if not se53_row.empty and not se1_row.empty:
            assert se53_row.iloc[0]["baseline_median"] == se1_row.iloc[0]["baseline_median"]


class TestBuildFeatures:
    def test_lag_columns_present(self):
        national = _make_national()
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        for lag in [1, 2, 3, 4]:
            assert f"lag_{lag}" in features.columns

    def test_fourier_columns_present(self):
        national = _make_national()
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        for k in [1, 2, 3]:
            assert f"sin_{k}" in features.columns
            assert f"cos_{k}" in features.columns

    def test_no_nan_in_lags(self):
        national = _make_national()
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        for lag in [1, 2, 3, 4]:
            assert not features[f"lag_{lag}"].isna().any()

    def test_holiday_flags(self):
        national = _make_national()
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        se1_rows = features[features["SE"] == 1]
        if not se1_rows.empty:
            assert se1_rows.iloc[0]["is_holiday"] == 1

    def test_drops_first_rows(self):
        national = _make_national()
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        assert len(features) == len(ratio_series) - 4  # max_lag = 4


class TestEstimateExceedanceProb:
    def test_below_all_quantiles(self):
        values = [10, 20, 30, 40, 50]
        levels = [0.1, 0.25, 0.5, 0.75, 0.9]
        prob = estimate_exceedance_prob(values, levels, 5)
        assert prob == pytest.approx(0.9, abs=0.01)

    def test_above_all_quantiles(self):
        values = [10, 20, 30, 40, 50]
        levels = [0.1, 0.25, 0.5, 0.75, 0.9]
        prob = estimate_exceedance_prob(values, levels, 55)
        assert prob == pytest.approx(0.1, abs=0.01)

    def test_at_median(self):
        values = [10, 20, 30, 40, 50]
        levels = [0.1, 0.25, 0.5, 0.75, 0.9]
        prob = estimate_exceedance_prob(values, levels, 30)
        assert prob == pytest.approx(0.5, abs=0.01)

    def test_interpolation(self):
        values = [10, 20, 30, 40, 50]
        levels = [0.1, 0.25, 0.5, 0.75, 0.9]
        prob = estimate_exceedance_prob(values, levels, 25)
        assert 0.3 < prob < 0.7


class TestClassifyForecastColor:
    def test_green(self):
        assert classify_color(5) == "green"

    def test_yellow(self):
        assert classify_color(15) == "yellow"

    def test_orange(self):
        assert classify_color(30) == "orange"

    def test_red(self):
        assert classify_color(60) == "red"

    def test_negative_is_green(self):
        assert classify_color(-10) == "green"


class TestNextWeek:
    def test_normal_advance(self):
        assert _next_week(2026, 10) == (2026, 11)

    def test_week_52_advances_to_53(self):
        assert _next_week(2026, 52) == (2026, 53)

    def test_year_boundary(self):
        assert _next_week(2026, 53) == (2027, 1)

    def test_week_1(self):
        assert _next_week(2026, 1) == (2026, 2)


@pytest.mark.skipif(not HAS_LGB, reason="lightgbm not installed")
class TestTrainAndPredict:
    def test_returns_4_horizons(self):
        from pipeline.forecast import train_and_predict
        national = _make_national(n_years=6)
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        result = train_and_predict(features, baselines_df, 2024, 50)
        assert len(result) == 4

    def test_horizon_structure(self):
        from pipeline.forecast import train_and_predict
        national = _make_national(n_years=6)
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        result = train_and_predict(features, baselines_df, 2024, 50)
        for h in result:
            assert "horizon" in h
            assert "year" in h
            assert "week" in h
            assert "proj" in h
            assert "color" in h
            assert "p_orange" in h
            assert "p_red" in h
            assert h["proj"] >= 0

    def test_probabilities_bounded(self):
        from pipeline.forecast import train_and_predict
        national = _make_national(n_years=6)
        baselines_df = _make_baselines()
        ratio_series = build_ratio_series(national, baselines_df)
        features = build_features(ratio_series)
        result = train_and_predict(features, baselines_df, 2024, 50)
        for h in result:
            assert 0 <= h["p_orange"] <= 1
            assert 0 <= h["p_red"] <= 1
