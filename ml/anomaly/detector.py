"""
ml/anomaly/detector.py

Anomaly detection for IndustrialGuard AI.

Experiment 2: Compare anomaly detection approaches and select the most appropriate
for the chosen dataset. Documented in DECISION_LOG.md DECISION-008.

Primary approach: Isolation Forest (fits unlabeled data, good for tabular manufacturing params).
Secondary: Statistical (IQR-based) per-parameter thresholds -- always available, interpretable.

The statistical approach provides parameter-level explanation ("Temperature is 2.3 IQR above normal").
The Isolation Forest provides a holistic anomaly score across all parameters.
Both outputs are included in the structured result so the Quality Analysis Agent can use both.
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("ml/models/artifacts")
EVAL_DIR = Path("ml/evaluation")

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

# Isolation Forest configuration
# contamination: expected fraction of outliers in training data
# Set from domain knowledge or dataset analysis -- NOT arbitrary
CONTAMINATION: str | float = "auto"   # "auto" uses standard heuristic; override after dataset analysis
RANDOM_STATE = 42

_iso_forest = None
_stat_thresholds = None
_feature_cols = None


# ── Training ───────────────────────────────────────────────────────────────────

def compute_statistical_thresholds(X: pd.DataFrame, factor: float = 2.5) -> dict:
    """
    Compute per-parameter statistical thresholds using IQR.
    factor=2.5 is moderate; adjust based on domain knowledge.
    Thresholds are data-derived -- do not fabricate industrial standards.
    """
    thresholds = {}
    for col in X.columns:
        Q1 = float(X[col].quantile(0.25))
        Q3 = float(X[col].quantile(0.75))
        IQR = Q3 - Q1
        thresholds[col] = {
            "Q1": Q1, "Q3": Q3, "IQR": IQR,
            "lower": Q1 - factor * IQR,
            "upper": Q3 + factor * IQR,
            "mean": float(X[col].mean()),
            "std": float(X[col].std()),
            "factor": factor,
        }
    return thresholds


def fit_isolation_forest(X: pd.DataFrame) -> IsolationForest:
    """Fit Isolation Forest on normal operating data (training set)."""
    iso = IsolationForest(
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_estimators=100,
    )
    iso.fit(X)
    return iso


def train_anomaly_detector(use_target_filtered: bool = True) -> None:
    """
    Train anomaly detector on training data.
    If use_target_filtered=True and a target column exists, fit only on NORMAL class samples.
    This gives the detector a cleaner view of "normal" operating conditions.
    """
    global _iso_forest, _stat_thresholds, _feature_cols

    # Load training data (prefer unscaled raw data for physical thresholding)
    train_path = PROCESSED_DIR / "train_raw.csv"
    if not train_path.exists():
        train_path = PROCESSED_DIR / "train.csv"
    if not train_path.exists():
        # Fall back to full processed dataset (anomaly-only mode, no labels)
        train_path = PROCESSED_DIR / "processed.csv"
    df = pd.read_csv(train_path)

    # Load feature columns
    feat_path = Path("data/features/feature_columns.json")
    if feat_path.exists():
        with open(feat_path) as f:
            feature_def = json.load(f)
        _feature_cols = feature_def["features"]
        target_col = feature_def.get("target")
    else:
        target_col = None
        _feature_cols = [c for c in df.columns if c != target_col]

    # Filter to normal class for fitting if labels available
    if use_target_filtered and target_col and target_col in df.columns:
        normal_df = df[df[target_col] == 0]
        logger.info(f"Fitting anomaly detector on NORMAL samples only: {len(normal_df)} records")
        X_fit = normal_df[_feature_cols]
    else:
        logger.info(f"Fitting anomaly detector on all training data: {len(df)} records")
        X_fit = df[_feature_cols]

    # Statistical thresholds
    _stat_thresholds = compute_statistical_thresholds(X_fit)
    joblib.dump(_stat_thresholds, ARTIFACTS_DIR / "stat_thresholds.pkl")

    # Isolation Forest
    _iso_forest = fit_isolation_forest(X_fit)
    joblib.dump(_iso_forest, ARTIFACTS_DIR / "isolation_forest.pkl")

    # Save threshold documentation
    with open(EVAL_DIR / "anomaly_thresholds.json", "w") as f:
        json.dump(_stat_thresholds, f, indent=2)

    logger.info("Anomaly detector training complete.")
    logger.info(f"Thresholds saved to ml/evaluation/anomaly_thresholds.json")
    logger.info("Update DECISION_LOG.md DECISION-008 with anomaly detection approach rationale.")


# ── Inference ──────────────────────────────────────────────────────────────────

def _load_detector():
    global _iso_forest, _stat_thresholds, _feature_cols
    iso_path = ARTIFACTS_DIR / "isolation_forest.pkl"
    thresh_path = ARTIFACTS_DIR / "stat_thresholds.pkl"
    if not iso_path.exists():
        raise FileNotFoundError("Anomaly detector not trained. Run ml/anomaly/detector.py first.")
    _iso_forest = joblib.load(iso_path)
    _stat_thresholds = joblib.load(thresh_path)
    feat_path = Path("data/features/feature_columns.json")
    with open(feat_path) as f:
        _feature_cols = json.load(f)["features"]


def detect_anomalies(record: dict) -> dict:
    """
    Detect anomalies in a single process record.

    Returns structured output consumed by Process Monitoring Agent and Quality Analysis Agent.

    Severity classification:
    - HIGH: Isolation Forest flags AND 2+ statistical violations
    - MEDIUM: Isolation Forest flags OR 2+ statistical violations
    - LOW: 1 statistical violation only
    - NORMAL: no violations detected
    """
    global _iso_forest, _stat_thresholds, _feature_cols

    if _iso_forest is None:
        _load_detector()

    df = pd.DataFrame([record])
    # Fill missing features
    for col in _feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    X = df[_feature_cols]

    # Isolation Forest score
    iso_score = float(_iso_forest.decision_function(X)[0])   # more negative = more anomalous
    iso_flag = bool(_iso_forest.predict(X)[0] == -1)

    # Statistical per-parameter violations
    stat_violations = []
    for col, thresh in _stat_thresholds.items():
        if col not in record:
            continue
        val = float(record[col])
        if val < thresh["lower"] or val > thresh["upper"]:
            deviation_iqr = 0.0
            if thresh["IQR"] > 0:
                mid = (thresh["Q1"] + thresh["Q3"]) / 2
                deviation_iqr = abs(val - mid) / thresh["IQR"]
            direction = "above" if val > thresh["upper"] else "below"
            stat_violations.append({
                "parameter": col,
                "value": round(val, 4),
                "normal_range": [round(thresh["lower"], 4), round(thresh["upper"], 4)],
                "direction": direction,
                "deviation_iqr_units": round(deviation_iqr, 2),
            })

    # Severity
    n_violations = len(stat_violations)
    if iso_flag and n_violations >= 2:
        severity = "HIGH"
    elif iso_flag or n_violations >= 2:
        severity = "MEDIUM"
    elif n_violations == 1:
        severity = "LOW"
    else:
        severity = "NORMAL"

    is_anomaly = severity != "NORMAL"

    return {
        "status": "ABNORMAL" if is_anomaly else "NORMAL",
        "is_anomaly": is_anomaly,
        "severity": severity,
        "isolation_forest_score": round(iso_score, 4),
        "isolation_forest_flag": iso_flag,
        "statistical_violations": stat_violations,
        "violation_count": n_violations,
        "note": (
            "Anomaly severity is data-derived from training distribution. "
            "It does not represent a certified industrial safety threshold."
        ),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_anomaly_detector()
