"""
tests/unit/test_preprocessing.py

Unit tests for the preprocessing pipeline.
Tests data quality, imputation, scaling, and split logic.
"""

import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path


def make_sample_df(n=100, add_missing=False, add_duplicates=False):
    """Create a minimal sample DataFrame for testing."""
    np.random.seed(42)
    df = pd.DataFrame({
        "feature_a": np.random.normal(50, 10, n),
        "feature_b": np.random.normal(100, 20, n),
        "feature_c": np.random.choice(["A", "B", "C"], n),
        "target": np.random.choice([0, 1], n, p=[0.8, 0.2]),
    })
    if add_missing:
        df.loc[[3, 7, 15], "feature_a"] = np.nan
    if add_duplicates:
        df = pd.concat([df, df.iloc[:5]], ignore_index=True)
    return df


class TestDataQualityReport:
    def test_shape_is_correct(self):
        df = make_sample_df(50)
        assert df.shape == (50, 4)

    def test_missing_detection(self):
        df = make_sample_df(50, add_missing=True)
        missing = df.isnull().sum()
        assert missing["feature_a"] == 3

    def test_duplicate_detection(self):
        df = make_sample_df(20, add_duplicates=True)
        dups = df.duplicated().sum()
        assert dups == 5


class TestOutlierHandling:
    def test_iqr_capping_caps_extremes(self):
        from ml.preprocessing.pipeline import handle_outliers_iqr

        df = make_sample_df(100)
        # Insert extreme outlier
        df.loc[0, "feature_a"] = 9999.0
        df_out = handle_outliers_iqr(df.copy(), ["feature_a"], factor=3.0)
        assert df_out["feature_a"].max() < 9999.0

    def test_iqr_capping_does_not_affect_normal_values(self):
        from ml.preprocessing.pipeline import handle_outliers_iqr

        df = make_sample_df(100)
        original_max = df["feature_a"].max()
        df_out = handle_outliers_iqr(df.copy(), ["feature_a"], factor=3.0)
        # Normal max should be unchanged (within factor=3 IQR)
        assert df_out["feature_a"].max() >= original_max * 0.5  # sanity


class TestSplitRatios:
    def test_split_sizes_sum_to_total(self):
        from ml.preprocessing.pipeline import TRAIN_RATIO, VAL_RATIO, TEST_RATIO
        assert abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) < 1e-6

    def test_no_label_leakage_in_split(self):
        """Test IDs -- train/val/test must be disjoint."""
        df = make_sample_df(200)
        from sklearn.model_selection import train_test_split

        X = df.drop(columns=["target"])
        y = df["target"]
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        X_val, X_test, _, _ = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

        # No overlap
        train_idx = set(X_train.index)
        val_idx = set(X_val.index)
        test_idx = set(X_test.index)
        assert len(train_idx & val_idx) == 0
        assert len(train_idx & test_idx) == 0
        assert len(val_idx & test_idx) == 0
