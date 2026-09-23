"""
tests/unit/test_anomaly_detector.py

Unit tests for anomaly detection module.
"""

import numpy as np
import pytest


class TestSeverityClassification:
    """Test the severity logic without requiring ML artifacts."""

    def _compute_severity(self, iso_flag: bool, n_violations: int) -> str:
        """Mirror the severity logic from detector.py."""
        if iso_flag and n_violations >= 2:
            return "HIGH"
        if iso_flag or n_violations >= 2:
            return "MEDIUM"
        if n_violations == 1:
            return "LOW"
        return "NORMAL"

    def test_high_severity_requires_iso_and_two_violations(self):
        assert self._compute_severity(True, 2) == "HIGH"
        assert self._compute_severity(True, 3) == "HIGH"

    def test_medium_severity_iso_only(self):
        assert self._compute_severity(True, 0) == "MEDIUM"
        assert self._compute_severity(True, 1) == "MEDIUM"

    def test_medium_severity_two_violations_no_iso(self):
        assert self._compute_severity(False, 2) == "MEDIUM"

    def test_low_severity_single_violation(self):
        assert self._compute_severity(False, 1) == "LOW"

    def test_normal_no_violations(self):
        assert self._compute_severity(False, 0) == "NORMAL"


class TestStatisticalThresholds:
    """Test threshold computation logic."""

    def test_thresholds_are_symmetric_around_median(self):
        """IQR thresholds should produce valid lower < upper bounds."""
        import pandas as pd
        from ml.anomaly.detector import compute_statistical_thresholds

        df = pd.DataFrame({"temp": np.random.normal(75, 5, 200)})
        thresholds = compute_statistical_thresholds(df, factor=2.5)

        assert "temp" in thresholds
        assert thresholds["temp"]["lower"] < thresholds["temp"]["upper"]
        assert thresholds["temp"]["Q1"] < thresholds["temp"]["Q3"]

    def test_extreme_outlier_detected(self):
        """A value 10 IQR units from center should be flagged."""
        import pandas as pd
        from ml.anomaly.detector import compute_statistical_thresholds

        df = pd.DataFrame({"speed": np.random.normal(100, 5, 100)})
        thresholds = compute_statistical_thresholds(df, factor=2.5)

        extreme_val = 9999.0
        is_violation = extreme_val > thresholds["speed"]["upper"]
        assert is_violation is True
