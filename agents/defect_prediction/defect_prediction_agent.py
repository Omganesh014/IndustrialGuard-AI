"""
agents/defect_prediction/defect_prediction_agent.py

Defect Prediction Agent -- Agent 3 of 4

Responsibilities:
- Receive structured output from Quality Analysis Agent
- Run trained defect prediction model (ML inference -- NOT LLM)
- Compute local SHAP explanation for this prediction
- Produce structured output for Process Optimization Agent

Input:  QualityAnalysisOutput dict (from Agent 2)
Output: DefectPredictionOutput dict (consumed by Agent 4)

Important:
- All numerical prediction work is done by the trained ML model
- LLM is not called here -- LLM reasoning is in the Optimization Agent
- Confidence/probability is from model.predict_proba, not fabricated
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_inference = None
_explainer = None


def _get_inference():
    global _inference
    if _inference is None:
        from ml.models.inference import predict
        _inference = predict
    return _inference


def _get_explainer():
    global _explainer
    if _explainer is None:
        try:
            import joblib
            import json
            from pathlib import Path
            from ml.explainability.shap_analysis import explain_single_prediction

            model_files = sorted(Path("ml/models").glob("defect_predictor_*.pkl"))
            scaler = joblib.load(Path("ml/models/artifacts/scaler.pkl"))
            with open("data/features/feature_columns.json") as f:
                feature_cols = json.load(f)["features"]
            model = joblib.load(model_files[-1])
            _explainer = lambda record: explain_single_prediction(model, record, feature_cols, scaler)
        except Exception as e:
            logger.warning(f"Explainer load failed: {e}. Local SHAP will be unavailable.")
            _explainer = lambda record: {"explanation_method": "unavailable", "local_contributions": []}
    return _explainer


def run(quality_output: dict) -> dict:
    """
    Main entry point for the Defect Prediction Agent.

    Args:
        quality_output: dict from Quality Analysis Agent

    Returns:
        DefectPredictionOutput dict consumed by Process Optimization Agent.
    """
    record = quality_output.get("input_record", {})
    record_id = quality_output.get("record_id")

    # Step 1: ML prediction (deterministic -- trained model only)
    try:
        predict = _get_inference()
        prediction_result = predict(record)
    except Exception as e:
        logger.error(f"Defect prediction failed: {e}")
        prediction_result = {
            "prediction": "ERROR",
            "probability": None,
            "model_version": "unknown",
            "error": str(e),
        }

    # Step 2: Local explainability
    try:
        explain = _get_explainer()
        explanation = explain(record)
    except Exception as e:
        logger.warning(f"Local explanation failed: {e}")
        explanation = {"explanation_method": "unavailable", "local_contributions": []}

    # Step 3: Combine anomaly + prediction context
    anomaly_severity = quality_output.get("anomaly_summary", {}).get("severity", "UNKNOWN")
    predicted_defective = prediction_result.get("prediction") == "DEFECTIVE"
    prob = prediction_result.get("probability")

    # Risk level: combine model probability + anomaly severity
    risk_level = _compute_risk_level(predicted_defective, prob, anomaly_severity)

    output = {
        "agent": "defect_prediction",
        "record_id": record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prediction": {
            "predicted_class": prediction_result.get("prediction"),
            "probability": prob,
            "model_version": prediction_result.get("model_version"),
            "is_defective": predicted_defective,
        },
        "explanation": explanation,
        "risk_level": risk_level,
        "anomaly_summary": quality_output.get("anomaly_summary"),
        "contributing_factors": quality_output.get("contributing_factors", []),
        "rag_evidence": quality_output.get("rag_evidence", []),
        "input_record": record,
        "note": (
            "Defect prediction produced by trained ML model. "
            "Probability reflects model confidence, not a certified industrial measurement. "
            "Requires human engineer review."
        ),
        "forward_to_optimization": True,
    }

    logger.info(
        f"[DefectPrediction] Record {record_id}: "
        f"prediction={prediction_result.get('prediction')}, "
        f"probability={prob}, "
        f"risk_level={risk_level}"
    )

    return output


def _compute_risk_level(
    is_defective: bool,
    probability: float | None,
    anomaly_severity: str,
) -> str:
    """
    Combine model prediction + anomaly severity into a single risk level.
    This is a rule-based combination -- not LLM-generated.
    """
    if is_defective and anomaly_severity in ("HIGH", "MEDIUM"):
        return "HIGH"
    if is_defective or anomaly_severity == "HIGH":
        return "ELEVATED"
    if anomaly_severity == "MEDIUM" or (probability is not None and probability > 0.4):
        return "MODERATE"
    if anomaly_severity == "LOW":
        return "LOW"
    return "NORMAL"
