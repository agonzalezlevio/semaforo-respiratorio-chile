"""Tests for pipeline.anomalies module."""

from pipeline.anomalies import ears_c2


class TestEarsC2:
    def test_flat_series_no_alerts(self):
        """A flat series should produce no alerts."""
        series = [100] * 20
        results = ears_c2(series)
        assert len(results) > 0
        assert all(not r["alert"] for r in results)

    def test_spike_detected(self):
        """A large spike after a variable baseline should trigger an alert."""
        # Need some variance in baseline so std > 0
        series = [95, 105, 98, 102, 97, 103, 99, 101, 96, 104, 100, 98, 102, 97, 103] + [500]
        results = ears_c2(series)
        # The last point should be an alert
        assert results[-1]["alert"] is True
        assert results[-1]["z"] > 2.0

    def test_zero_std_returns_z_zero(self):
        """When baseline has zero std, z should be 0."""
        series = [50] * 15 + [50]  # all identical
        results = ears_c2(series)
        assert all(r["z"] == 0.0 for r in results)

    def test_output_length(self):
        """Output length should be len(series) - window - guard."""
        series = list(range(30))
        results = ears_c2(series, window=7, guard=2)
        expected_len = len(series) - 7 - 2
        assert len(results) == expected_len

    def test_custom_threshold(self):
        """Higher threshold should produce fewer alerts."""
        series = [100] * 12 + [200, 300, 500]
        alerts_low = ears_c2(series, threshold=1.0)
        alerts_high = ears_c2(series, threshold=3.0)
        low_count = sum(1 for r in alerts_low if r["alert"])
        high_count = sum(1 for r in alerts_high if r["alert"])
        assert low_count >= high_count

    def test_index_matches_series_position(self):
        """Returned index should match the position in the original series."""
        series = [100] * 20
        results = ears_c2(series, window=7, guard=2)
        assert results[0]["index"] == 9  # window + guard
        assert results[-1]["index"] == 19  # last element
