"""Tests for pipeline.compute module."""

import math

from pipeline.compute import classify_color, compute_change_pct, compute_zscore


class TestClassifyColor:
    def test_green_negative(self):
        assert classify_color(-5.0) == "green"

    def test_green_zero(self):
        assert classify_color(0.0) == "green"

    def test_green_just_under(self):
        assert classify_color(9.99) == "green"

    def test_yellow_at_boundary(self):
        assert classify_color(10.0) == "yellow"

    def test_yellow_mid(self):
        assert classify_color(20.0) == "yellow"

    def test_orange_at_boundary(self):
        assert classify_color(25.0) == "orange"

    def test_orange_mid(self):
        assert classify_color(40.0) == "orange"

    def test_red_at_boundary(self):
        assert classify_color(50.0) == "red"

    def test_red_extreme(self):
        assert classify_color(200.0) == "red"

    def test_nan_returns_no_data(self):
        assert classify_color(float("nan")) == "no_data"

    def test_none_returns_no_data(self):
        assert classify_color(None) == "no_data"


class TestComputeChangePct:
    def test_no_change(self):
        assert compute_change_pct(100, 100) == 0.0

    def test_increase(self):
        result = compute_change_pct(150, 100)
        assert abs(result - 50.0) < 0.01

    def test_decrease(self):
        result = compute_change_pct(80, 100)
        assert abs(result - (-20.0)) < 0.01

    def test_zero_median_returns_nan(self):
        result = compute_change_pct(100, 0)
        assert math.isnan(result)

    def test_nan_median_returns_nan(self):
        result = compute_change_pct(100, float("nan"))
        assert math.isnan(result)

    def test_none_median_returns_nan(self):
        result = compute_change_pct(100, None)
        assert math.isnan(result)


class TestComputeZscore:
    def test_at_mean(self):
        assert compute_zscore(50, [40, 50, 60]) == 0.0

    def test_above_mean(self):
        z = compute_zscore(70, [40, 50, 60])
        assert z > 0

    def test_below_mean(self):
        z = compute_zscore(30, [40, 50, 60])
        assert z < 0

    def test_empty_ref_returns_zero(self):
        assert compute_zscore(100, []) == 0.0

    def test_zero_std_returns_zero(self):
        assert compute_zscore(50, [50, 50, 50]) == 0.0
