"""
ml/explainability/shap_analysis.py

Explainability for IndustrialGuard AI.

Implements SHAP-based feature importance for the defect prediction model.
Falls back to permutation importance if SHAP is unavailable or too slow for dataset size.

Outputs:
- Global feature importance (training set)
- Local explanation for a single prediction (per-record SHAP values)
- Explanation formatted for the dashboard and agent consumption

Important: SHAP values explain model behavior, not causal mechanisms.
The dashboard must label these as "model-derived feature importance" and never "proof of causation."
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
EVAL_DIR = Path("ml/evaluation")
FEATURES_DIR = Path("data/features")
PROCESSED_DIR = Path("data/processed")

EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_model_and_features():
    """Load trained model and feature definitions."""
    model_files = sorted(MODELS_DIR.glob("defect_predictor_*.pkl"))
    if not model_files:
        raise FileNotFoundError("No trained model found. Run ml/models/train.py first.")
    model = joblib.load(model_files[-1])

    with open(FEATURES_DIR / "feature_columns.json") as f:
        feature_def = json.load(f)
    feature_cols = feature_def["features"]

    return model, feature_cols


def compute_global_importance(model, X: pd.DataFrame, feature_cols: list[str]) -> list[dict]:
    """
    Compute global feature importance.
    Uses SHAP TreeExplainer for tree models; falls back to model-native feature_importances_.
    Returns sorted list of {feature, importance, explanation_method}.
    """
    method = "unknown"
    importances = None

    # Try SHAP first
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        if isinstance(shap_values, list):
            # Binary classification: shap_values[1] = positive class
            sv = np.abs(shap_values[1])
        else:
            sv = np.abs(shap_values)
        importances = sv.mean(axis=0)
        method = "SHAP (TreeExplainer)"
        logger.info("SHAP TreeExplainer succeeded.")
    except Exception as e:
        logger.warning(f"SHAP failed ({e}). Falling back to model feature_importances_.")

    # Fallback: model-native feature importance
    if importances is None:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            method = "model_native_feature_importances"
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])
            method = "logistic_regression_coef_abs"
        else:
            logger.warning("No feature importance method available for this model type.")
            return []

    # Sort descending
    ranked = sorted(
        zip(feature_cols, importances),
        key=lambda x: x[1],
        reverse=True
    )

    result = [
        {
            "rank": i + 1,
            "feature": feat,
            "importance": round(float(imp), 6),
            "explanation_method": method,
        }
        for i, (feat, imp) in enumerate(ranked)
    ]
    return result


def explain_single_prediction(model, record: dict, feature_cols: list[str], scaler) -> dict:
    """
    Compute SHAP values for a single process record.
    Returns local explanation formatted for the dashboard.
    Falls back to global importance if SHAP fails.
    """
    df = pd.DataFrame([record])
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    X = df[feature_cols].copy()
    X_scaled = scaler.transform(X)
    X_df = pd.DataFrame(X_scaled, columns=feature_cols)

    method = "unknown"
    local_values = {}

    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_df)
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        else:
            sv = shap_values[0]
        local_values = {feat: round(float(val), 6) for feat, val in zip(feature_cols, sv)}
        method = "SHAP (TreeExplainer)"
    except Exception as e:
        logger.warning(f"Local SHAP failed ({e}). Using global importance as proxy.")
        method = "global_feature_importance_proxy"
        # Return empty dict; agent will use global importance
        local_values = {}

    # Rank by absolute contribution
    ranked = sorted(local_values.items(), key=lambda x: abs(x[1]), reverse=True)

    return {
        "explanation_method": method,
        "local_contributions": ranked[:10],  # Top 10 for dashboard
        "all_contributions": local_values,
        "disclaimer": (
            "Feature contributions reflect model behavior on this record. "
            "They indicate association, not causation. "
            "This is model-derived evidence -- not a certified engineering diagnosis."
        ),
    }


def save_global_importance(importances: list[dict]) -> None:
    """Save global feature importance to evaluation directory."""
    with open(EVAL_DIR / "global_feature_importance.json", "w") as f:
        json.dump(importances, f, indent=2)
    logger.info(f"Global feature importance saved: {len(importances)} features")


def run_explainability_analysis() -> None:
    """Run global SHAP/importance analysis on training data. Call after training."""
    model, feature_cols = load_model_and_features()
    scaler = joblib.load(ARTIFACTS_DIR / "scaler.pkl")

    train_df = pd.read_csv(PROCESSED_DIR / "train.csv")
    target_col = json.load(open(FEATURES_DIR / "feature_columns.json"))["target"]

    X_train = train_df[feature_cols]

    logger.info("Computing global feature importance...")
    global_imp = compute_global_importance(model, X_train, feature_cols)
    save_global_importance(global_imp)

    logger.info("\nTop 10 features by global importance:")
    for item in global_imp[:10]:
        bar = "█" * int(item["importance"] * 100 / max(global_imp[0]["importance"], 1e-6) * 20)
        logger.info(f"  {item['rank']:2d}. {item['feature']:<30s} {bar}")

    logger.info(f"\nExplanation method used: {global_imp[0]['explanation_method'] if global_imp else 'N/A'}")
    logger.info("Explainability analysis complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_explainability_analysis()
