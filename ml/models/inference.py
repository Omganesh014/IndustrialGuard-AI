"""
ml/models/inference.py

Inference module for defect prediction at runtime.

This module is called by the Defect Prediction Agent.
It loads the trained model and scaler, runs prediction, and returns structured output.

Returns structured JSON -- never free text -- so agents can consume it deterministically.
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODELS_DIR = Path("ml/models")
ARTIFACTS_DIR = MODELS_DIR / "artifacts"
FEATURES_DIR = Path("data/features")

# Cached loaded artifacts (lazy-loaded on first call)
_model = None
_scaler = None
_encoders = None
_feature_cols = None
_model_version = None


def _load_artifacts():
    """Lazy-load model and preprocessing artifacts."""
    global _model, _scaler, _encoders, _feature_cols, _model_version

    # Find latest model version
    model_files = sorted(MODELS_DIR.glob("defect_predictor_*.pkl"))
    if not model_files:
        raise FileNotFoundError(
            "No trained model found in ml/models/. Run ml/models/train.py first."
        )
    latest = model_files[-1]
    _model_version = latest.stem.replace("defect_predictor_", "")

    _model = joblib.load(latest)
    _scaler = joblib.load(ARTIFACTS_DIR / "scaler.pkl")
    encoders_path = ARTIFACTS_DIR / "label_encoders.pkl"
    _encoders = joblib.load(encoders_path) if encoders_path.exists() else {}

    with open(FEATURES_DIR / "feature_columns.json") as f:
        feature_def = json.load(f)
    _feature_cols = feature_def["features"]

    logger.info(f"Loaded model version: {_model_version}, features: {len(_feature_cols)}")


def predict(record: dict) -> dict:
    """
    Run defect prediction on a single process record.

    Args:
        record: dict of {feature_name: value} -- raw process parameters

    Returns:
        dict with:
        - prediction: "DEFECTIVE" | "NORMAL"
        - probability: float (0-1) -- model confidence
        - model_version: str
        - input_features: dict (sanitized copy of input)
        - note: data provenance label
    """
    global _model, _scaler, _encoders, _feature_cols, _model_version

    if _model is None:
        _load_artifacts()

    # Build feature vector in correct column order
    df = pd.DataFrame([record])

    # Encode categorical columns
    for col, le in (_encoders or {}).items():
        if col in df.columns:
            try:
                df[col] = le.transform(df[col].astype(str))
            except ValueError as e:
                logger.warning(f"Unknown category in {col}: {e}. Using most frequent fallback.")
                df[col] = le.transform([le.classes_[0]])

    # Ensure all feature columns present; fill missing with 0 (logged as anomaly)
    missing_cols = [c for c in _feature_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing features at inference: {missing_cols} -- filled with 0")
    for col in missing_cols:
        df[col] = 0.0

    X = df[_feature_cols].copy()
    X_scaled = _scaler.transform(X)

    pred_class = int(_model.predict(X_scaled)[0])
    prob = float(_model.predict_proba(X_scaled)[0][1]) if hasattr(_model, "predict_proba") else None

    return {
        "prediction": "DEFECTIVE" if pred_class == 1 else "NORMAL",
        "predicted_class": pred_class,
        "probability": round(prob, 4) if prob is not None else None,
        "model_version": _model_version,
        "input_features": {k: record.get(k) for k in _feature_cols},
        "data_source_label": "REAL PUBLIC DATA",  # update if using synthetic stream
        "note": (
            "This is a model prediction, not a certified engineering result. "
            "Requires human engineer review before any process action."
        ),
    }


def batch_predict(records: list[dict]) -> list[dict]:
    """Run prediction on multiple records. Returns list of prediction dicts."""
    return [predict(r) for r in records]
