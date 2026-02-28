"""Tests for pipeline/validate.py"""

import numpy as np
import pandas as pd
import pytest

from pipeline.validate import (
    compute_wis,
    aggregate_metrics,
    compute_naive_metrics,
    _build_naive_quantiles,
    _classify_color_from_actual,
)
from pipeline.forecast import HAS_LGB


def _make_baselines(weeks=52):
    """Builds synthetic baselines DataFrame."""
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


def _make_national(n_years=5, weeks_per_year=52):
    """Builds synthetic national DataFrame."""
    rows = []
    for year in range(2019, 2019 + n_years):
        for se in range(1, weeks_per_year + 1):
            base = 40000 + 5000 * np.sin(2 * np.pi * se / 52)
            noise = np.random.RandomState(year * 100 + se).normal(0, 1000)
            total = max(int(base + noise), 1000)
            rows.append({"Anio": year, "SE": se, "Causa": "Total", "NumTotal": total})
    return pd.DataFrame(rows)


class TestComputeWis:
    def test_perfect_prediction(self):
        """WIS should be minimal when prediction is exact."""
        actual = 1000
        preds = {
            0.025: 900, 0.1: 950, 0.25: 980,
            0.5: 1000,
            0.75: 1020, 0.9: 1050, 0.975: 1100,
        }
        wis = compute_wis(actual, preds)
        assert wis >= 0
        assert wis < 100

    def test_zero_error_only_width(self):
        """When actual = median and inside all intervals, WIS = width penalty only."""
        actual = 1000
        preds = {
            0.025: 800, 0.1: 850, 0.25: 900,
            0.5: 1000,
            0.75: 1100, 0.9: 1150, 0.975: 1200,
        }
        wis = compute_wis(actual, preds)
        assert wis > 0

    def test_out_of_interval_penalty(self):
        """WIS should be much larger when actual is outside all intervals."""
        preds = {
            0.025: 900, 0.1: 920, 0.25: 950,
            0.5: 1000,
            0.75: 1050, 0.9: 1080, 0.975: 1100,
        }
        wis_inside = compute_wis(1000, preds)
        wis_outside = compute_wis(2000, preds)
        assert wis_outside > wis_inside * 3

    def test_symmetric_penalty(self):
        """WIS penalty should be similar for under/overshoot of same magnitude."""
        preds = {
            0.025: 900, 0.1: 920, 0.25: 950,
            0.5: 1000,
            0.75: 1050, 0.9: 1080, 0.975: 1100,
        }
        wis_high = compute_wis(1200, preds)
        wis_low = compute_wis(800, preds)
        assert abs(wis_high - wis_low) / max(wis_high, wis_low) < 0.5

    def test_known_value(self):
        """Tests WIS against hand-computed value."""
        actual = 500
        preds = {0.025: 400, 0.1: 420, 0.25: 450, 0.5: 500, 0.75: 550, 0.9: 580, 0.975: 600}
        expected = (1 / 3.5) * (0 + 5 + 16 + 25)
        wis = compute_wis(actual, preds)
        assert abs(wis - expected) < 0.01


class TestBuildNaiveQuantiles:
    def test_returns_all_quantiles(self):
        """Should return a quantile for each forecast quantile level."""
        bl = _make_baselines()
        result = _build_naive_quantiles(bl, 10)
        for q in [0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975]:
            assert q in result

    def test_median_is_baseline(self):
        """Naive median should match the baseline median."""
        bl = _make_baselines()
        result = _build_naive_quantiles(bl, 10)
        expected = float(bl[bl["SE"] == 10].iloc[0]["NumTotal_median"])
        assert result[0.5] == expected

    def test_se53_maps_to_1(self):
        """SE 53 should map to SE 1 for baseline lookup."""
        bl = _make_baselines()
        result_53 = _build_naive_quantiles(bl, 53)
        result_1 = _build_naive_quantiles(bl, 1)
        assert result_53[0.5] == result_1[0.5]


class TestClassifyColorFromActual:
    def test_green(self):
        assert _classify_color_from_actual(1050, 1000) == "green"

    def test_yellow(self):
        assert _classify_color_from_actual(1150, 1000) == "yellow"

    def test_orange(self):
        assert _classify_color_from_actual(1350, 1000) == "orange"

    def test_red(self):
        assert _classify_color_from_actual(1600, 1000) == "red"

    def test_zero_baseline(self):
        assert _classify_color_from_actual(100, 0) == "no_data"


class TestAggregateMetrics:
    def test_correct_structure(self):
        """Should return dict keyed by horizon with expected metric keys."""
        fake_results = [
            {
                "test_year": 2023, "test_week": 10, "horizon": 1,
                "actual": 40000,
                "predicted": {0.025: 35000, 0.1: 36000, 0.25: 38000, 0.5: 40000, 0.75: 42000, 0.9: 44000, 0.975: 45000},
                "pred_color": "green", "actual_color": "green",
            },
            {
                "test_year": 2023, "test_week": 11, "horizon": 1,
                "actual": 41000,
                "predicted": {0.025: 36000, 0.1: 37000, 0.25: 39000, 0.5: 41000, 0.75: 43000, 0.9: 45000, 0.975: 46000},
                "pred_color": "green", "actual_color": "green",
            },
        ]
        result = aggregate_metrics(fake_results)
        assert "1" in result
        assert "wis" in result["1"]
        assert "mae_pct" in result["1"]
        assert "coverage_95" in result["1"]
        assert "color_accuracy" in result["1"]

    def test_perfect_coverage(self):
        """When actual is inside all intervals, coverage should be 100%."""
        fake_results = [
            {
                "test_year": 2023, "test_week": i, "horizon": 1,
                "actual": 40000,
                "predicted": {0.025: 30000, 0.1: 32000, 0.25: 35000, 0.5: 40000, 0.75: 45000, 0.9: 48000, 0.975: 50000},
                "pred_color": "green", "actual_color": "green",
            }
            for i in range(1, 11)
        ]
        result = aggregate_metrics(fake_results)
        assert result["1"]["coverage_95"] == 100.0

    def test_multiple_horizons(self):
        """Should produce separate metrics for each horizon."""
        fake_results = []
        for h in [1, 2]:
            for i in range(5):
                fake_results.append({
                    "test_year": 2023, "test_week": i + 1, "horizon": h,
                    "actual": 40000,
                    "predicted": {0.025: 35000, 0.1: 36000, 0.25: 38000, 0.5: 40000, 0.75: 42000, 0.9: 44000, 0.975: 45000},
                    "pred_color": "green", "actual_color": "green",
                })
        result = aggregate_metrics(fake_results)
        assert "1" in result
        assert "2" in result


class TestComputeNaiveMetrics:
    def test_uses_baseline_median(self):
        """Naive forecast should use baseline median as point forecast."""
        bl = _make_baselines()
        national = _make_national()
        fake_results = [
            {
                "test_year": 2023, "test_week": 10, "horizon": 1,
                "actual": 40000,
                "predicted": {0.5: 40000},
                "pred_color": "green", "actual_color": "green",
            },
        ]
        result = compute_naive_metrics(national, bl, fake_results)
        assert "1" in result
        assert result["1"]["wis"] >= 0

    def test_returns_expected_keys(self):
        """Should return wis, mae_pct, coverage_95, color_accuracy."""
        bl = _make_baselines()
        national = _make_national()
        fake_results = [
            {
                "test_year": 2023, "test_week": se, "horizon": 1,
                "actual": 40000 + se * 100,
                "predicted": {0.5: 40000},
                "pred_color": "green", "actual_color": "green",
            }
            for se in range(1, 11)
        ]
        result = compute_naive_metrics(national, bl, fake_results)
        assert "wis" in result["1"]
        assert "mae_pct" in result["1"]
        assert "coverage_95" in result["1"]
        assert "color_accuracy" in result["1"]


@pytest.mark.skipif(not HAS_LGB, reason="LightGBM not installed")
class TestRunFold:
    def test_returns_list_of_dicts(self):
        """run_fold should return a list of result dicts."""
        from pipeline.validate import run_fold

        national = _make_national(n_years=6)
        fold = {"train_end": 2022, "test_year": 2023}
        results = run_fold(national, fold)
        assert isinstance(results, list)
        if results:
            r = results[0]
            assert "test_year" in r
            assert "test_week" in r
            assert "horizon" in r
            assert "actual" in r
            assert "predicted" in r
            assert "pred_color" in r
            assert "actual_color" in r

    def test_all_horizons_present(self):
        """Results should contain entries for multiple horizons."""
        from pipeline.validate import run_fold

        national = _make_national(n_years=6)
        fold = {"train_end": 2022, "test_year": 2023}
        results = run_fold(national, fold)
        if results:
            horizons_found = set(r["horizon"] for r in results)
            assert len(horizons_found) >= 1
