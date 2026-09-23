"""
ml/preprocessing/pipeline.py

Data preprocessing pipeline for IndustrialGuard AI.

Responsibilities:
- Load raw dataset (CSV or Parquet)
- Handle missing values
- Handle duplicates
- Identify and handle outliers (IQR method, documented)
- Encode categorical features
- Scale numerical features (fit on TRAIN ONLY — no leakage)
- Engineer features
- Produce train/validation/test splits
- Save processed datasets and scaler artifacts

All preprocessing parameters are fit on the training set only.
Scaler and encoder objects are saved for use at inference time.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
FEATURES_DIR = Path("data/features")
ARTIFACTS_DIR = Path("ml/models/artifacts")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Configuration ──────────────────────────────────────────────────────────────
# Fill these after Gate B — dataset-specific
DATASET_FILENAME = os.getenv("DATASET_FILENAME", "dataset.csv")
TARGET_COLUMN = os.getenv("TARGET_COLUMN", "target")  # defect label or None
ID_COLUMNS: list[str] = []       # columns to drop (IDs, timestamps used only for ordering)
CATEGORICAL_COLUMNS: list[str] = []  # fill after dataset inspection
NUMERICAL_COLUMNS: list[str] = []    # fill after dataset inspection

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
RANDOM_STATE = 42


# ── Pipeline ───────────────────────────────────────────────────────────────────

def load_raw_data(filename: str = DATASET_FILENAME) -> pd.DataFrame:
    """Load the raw dataset. Supports CSV and Parquet."""
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}. "
            "Place the dataset in data/raw/ and set DATASET_FILENAME in .env."
        )
    if filename.endswith(".parquet"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    logger.info(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns")
    logger.info(f"Columns: {list(df.columns)}")
    return df


def report_data_quality(df: pd.DataFrame) -> dict:
    """Produce a data quality report. Logged but never fabricated."""
    report = {
        "shape": df.shape,
        "missing_counts": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
    if TARGET_COLUMN and TARGET_COLUMN in df.columns:
        report["target_distribution"] = df[TARGET_COLUMN].value_counts().to_dict()
    logger.info(f"Data quality report: {json.dumps(report, indent=2)}")
    return report


def handle_missing_values(df: pd.DataFrame, fit: bool = True, imputer=None):
    """
    Impute missing values.
    - Numerical: median imputation (robust to outliers)
    - Categorical: most frequent
    fit=True during training; fit=False + pass imputer at inference.
    """
    num_cols = [c for c in NUMERICAL_COLUMNS if c in df.columns]
    cat_cols = [c for c in CATEGORICAL_COLUMNS if c in df.columns]

    if fit:
        num_imputer = SimpleImputer(strategy="median")
        cat_imputer = SimpleImputer(strategy="most_frequent")
        if num_cols:
            df[num_cols] = num_imputer.fit_transform(df[num_cols])
        if cat_cols:
            df[cat_cols] = cat_imputer.fit_transform(df[cat_cols])
        joblib.dump(num_imputer, ARTIFACTS_DIR / "num_imputer.pkl")
        joblib.dump(cat_imputer, ARTIFACTS_DIR / "cat_imputer.pkl")
        return df, num_imputer, cat_imputer
    else:
        num_imputer, cat_imputer = imputer
        if num_cols:
            df[num_cols] = num_imputer.transform(df[num_cols])
        if cat_cols:
            df[cat_cols] = cat_imputer.transform(df[cat_cols])
        return df


def handle_outliers_iqr(df: pd.DataFrame, columns: list[str], factor: float = 3.0) -> pd.DataFrame:
    """
    Cap outliers using IQR method with a configurable factor.
    Factor=3.0 is conservative (only extreme outliers capped).
    Documents which values were capped in logs.
    """
    for col in columns:
        if col not in df.columns:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        n_capped = ((df[col] < lower) | (df[col] > upper)).sum()
        if n_capped > 0:
            logger.info(f"Outlier capping — {col}: {n_capped} values capped to [{lower:.3f}, {upper:.3f}]")
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df


def encode_categorical(df: pd.DataFrame, fit: bool = True, encoders: dict | None = None):
    """
    Label-encode categorical columns.
    fit=True during training; pass encoders at inference.
    """
    if fit:
        encoders = {}
        for col in CATEGORICAL_COLUMNS:
            if col not in df.columns:
                continue
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
        joblib.dump(encoders, ARTIFACTS_DIR / "label_encoders.pkl")
        return df, encoders
    else:
        for col, le in (encoders or {}).items():
            if col in df.columns:
                df[col] = le.transform(df[col].astype(str))
        return df


def scale_features(df: pd.DataFrame, feature_cols: list[str], fit: bool = True, scaler=None):
    """
    StandardScaler applied to numerical features.
    MUST be fit on training data only.
    """
    if fit:
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
        joblib.dump(scaler, ARTIFACTS_DIR / "scaler.pkl")
        return df, scaler
    else:
        df[feature_cols] = scaler.transform(df[feature_cols])
        return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering.
    Fill this after dataset inspection.
    Examples (dataset-specific — do not apply blindly):
    - Rolling means if timestamps present
    - Ratio features if domain knowledge supports them
    - Interaction terms if correlation analysis shows relevance
    All features must be justified by EDA or domain knowledge.
    """
    # TODO: implement after Gate B dataset analysis
    # Example (do not uncomment without validation):
    # if "temperature" in df.columns and "pressure" in df.columns:
    #     df["temp_pressure_ratio"] = df["temperature"] / (df["pressure"] + 1e-6)
    logger.info("Feature engineering: placeholder — implement after dataset inspection")
    return df


def split_data(df: pd.DataFrame, target_col: str):
    """
    Stratified train/val/test split.
    Stratify on target if it is a classification label.
    """
    X = df.drop(columns=[target_col] + [c for c in ID_COLUMNS if c in df.columns])
    y = df[target_col]

    stratify = y if y.nunique() <= 20 else None  # stratify for classification targets

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(VAL_RATIO + TEST_RATIO), random_state=RANDOM_STATE, stratify=stratify
    )
    val_relative = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=(1 - val_relative), random_state=RANDOM_STATE,
        stratify=y_temp if stratify is not None else None
    )

    logger.info(f"Split sizes — Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test


def save_feature_definitions(feature_cols: list[str]) -> None:
    """Save feature list for use at inference time."""
    with open(FEATURES_DIR / "feature_columns.json", "w") as f:
        json.dump({"features": feature_cols, "target": TARGET_COLUMN}, f, indent=2)
    logger.info(f"Feature definitions saved: {len(feature_cols)} features")


def run_pipeline():
    """Full preprocessing pipeline. Run this before model training."""
    df = load_raw_data()
    quality_report = report_data_quality(df)

    # Save quality report
    with open(PROCESSED_DIR / "data_quality_report.json", "w") as f:
        json.dump(quality_report, f, indent=2, default=str)

    # Remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Dropped {before - len(df)} duplicate rows")

    # Impute missing values
    df, num_imputer, cat_imputer = handle_missing_values(df, fit=True)

    # Outlier handling (numerical only)
    df = handle_outliers_iqr(df, NUMERICAL_COLUMNS)

    # Encode categorical
    df, encoders = encode_categorical(df, fit=True)

    # Feature engineering
    df = engineer_features(df)

    if TARGET_COLUMN and TARGET_COLUMN in df.columns:
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(df, TARGET_COLUMN)

        feature_cols = list(X_train.columns)
        save_feature_definitions(feature_cols)

        # Scale (fit on train only)
        X_train, scaler = scale_features(X_train, feature_cols, fit=True)
        X_val = scale_features(X_val, feature_cols, fit=False, scaler=scaler)
        X_test = scale_features(X_test, feature_cols, fit=False, scaler=scaler)

        # Save splits
        for name, X, y in [("train", X_train, y_train), ("val", X_val, y_val), ("test", X_test, y_test)]:
            out = X.copy()
            out[TARGET_COLUMN] = y.values
            out.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)

        logger.info("Preprocessing pipeline complete. Splits saved to data/processed/")
    else:
        logger.warning(
            "TARGET_COLUMN not found or not set. "
            "Saving unsplit processed dataset for anomaly detection use."
        )
        feature_cols = [c for c in df.columns if c not in ID_COLUMNS]
        save_feature_definitions(feature_cols)
        df, scaler = scale_features(df, feature_cols, fit=True)
        df.to_csv(PROCESSED_DIR / "processed.csv", index=False)

    logger.info("All preprocessing artifacts saved to ml/models/artifacts/")


if __name__ == "__main__":
    run_pipeline()
