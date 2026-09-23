"""
agents/optimization/process_optimization_agent.py

Process Optimization Agent — Agent 4 of 4

Responsibilities:
- Receive DefectPredictionOutput from Agent 3
- Generate corrective recommendations derived from ONE of three evidential bases:
    (a) Rule-based: parameter outside validated operating range → recommend moving toward range
    (b) Historical: find past low-defect operating conditions for similar process states
    (c) What-if inference: perturb a feature in the trained model → show probability shift
- Retrieve RAG context to support recommendations
- Call Granite/LLM to NARRATE the recommendation (synthesis only — no invented numbers)
- Produce structured RecommendationOutput for the API / dashboard

CRITICAL RULE:
The LLM must NOT invent numerical parameter adjustments.
Every numerical suggestion must be traceable to (a), (b), or (c) above.
When evidence is insufficient, the system must say so explicitly — never fabricate.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("ml/models/artifacts")
FEATURES_DIR = Path("data/features")
EVAL_DIR = Path("ml/evaluation")

# Operating range documentation — loaded from validated range file
# These ranges must come from the dataset (e.g., normal-class percentiles)
# NOT from fabricated "industry standard" numbers
OPERATING_RANGES_PATH = EVAL_DIR / "operating_ranges.json"

_model = None
_scaler = None
_feature_cols = None
_operating_ranges = None
_historical_data = None

_rag_retriever = None
_llm_client = None


def _get_rag():
    global _rag_retriever
    if _rag_retriever is None:
        from rag.retrieval.retriever import retrieve
        _rag_retriever = retrieve
    return _rag_retriever


def _get_llm():
    global _llm_client
    if _llm_client is None:
        from backend.services.granite_client import generate_narrative
        _llm_client = generate_narrative
    return _llm_client


def _load_artifacts():
    global _model, _scaler, _feature_cols, _operating_ranges, _historical_data

    model_files = sorted(Path("ml/models").glob("defect_predictor_*.pkl"))
    if model_files:
        _model = joblib.load(model_files[-1])
    _scaler = joblib.load(ARTIFACTS_DIR / "scaler.pkl")

    with open(FEATURES_DIR / "feature_columns.json") as f:
        _feature_cols = json.load(f)["features"]

    if OPERATING_RANGES_PATH.exists():
        with open(OPERATING_RANGES_PATH) as f:
            _operating_ranges = json.load(f)
    else:
        logger.warning("Operating ranges file not found. Rule-based recommendations will be limited.")
        _operating_ranges = {}

    # Load historical normal data for approach (b)
    hist_path = PROCESSED_DIR / "train.csv"
    if hist_path.exists():
        df = pd.read_csv(hist_path)
        target_col = json.load(open(FEATURES_DIR / "feature_columns.json")).get("target")
        if target_col and target_col in df.columns:
            _historical_data = df[df[target_col] == 0][_feature_cols]
        else:
            _historical_data = df[_feature_cols]


def _generate_rule_based_recommendations(
    record: dict, violations: list[dict]
) -> list[dict]:
    """
    Approach (a): Rule-based recommendations.
    For each violated parameter, recommend moving it toward the validated operating range.
    """
    if _operating_ranges is None:
        _load_artifacts()

    recommendations = []
    for violation in violations:
        param = violation["parameter"]
        if param not in _operating_ranges:
            continue
        op_range = _operating_ranges[param]
        current_val = float(record.get(param, 0))
        target_val = (op_range["normal_low"] + op_range["normal_high"]) / 2

        recommendations.append({
            "action": f"Adjust {param} toward normal operating range",
            "parameter": param,
            "current_value": round(current_val, 4),
            "suggested_direction": violation.get("direction", "unknown"),
            "target_range": [op_range["normal_low"], op_range["normal_high"]],
            "basis": "rule_based_operating_range",
            "evidence": f"{param} is currently {violation['direction']} normal range",
            "uncertainty": "low" if op_range.get("data_derived") else "high",
        })

    return recommendations


def _generate_whatif_recommendations(
    record: dict, top_features: list[str]
) -> list[dict]:
    """
    Approach (c): What-if inference.
    Perturb each top feature ±1 std from training distribution.
    Report predicted probability change.
    Returns empty list if model unavailable.
    """
    if _model is None or _scaler is None:
        return []

    try:
        # Compute training std from scaler
        # Scaler was fit on training data; std is available
        if not hasattr(_scaler, "scale_"):
            return []

        feature_idx = {f: i for i, f in enumerate(_feature_cols)}
        base_df = pd.DataFrame([record])
        for col in _feature_cols:
            if col not in base_df.columns:
                base_df[col] = 0.0
        X_base = base_df[_feature_cols].copy()
        X_base_scaled = _scaler.transform(X_base)
        base_prob = float(_model.predict_proba(X_base_scaled)[0][1])

        recommendations = []
        for feat in top_features[:3]:  # limit to top 3 features for performance
            if feat not in feature_idx:
                continue
            idx = feature_idx[feat]
            std = float(_scaler.scale_[idx])

            best_delta = None
            best_prob_after = base_prob
            best_direction = None

            for delta in [-1.0, -0.5, +0.5, +1.0]:  # in scaled units
                X_perturbed = X_base_scaled.copy()
                X_perturbed[0, idx] += delta
                prob_after = float(_model.predict_proba(X_perturbed)[0][1])
                if prob_after < best_prob_after:
                    best_prob_after = prob_after
                    best_delta = delta
                    best_direction = "decrease" if delta < 0 else "increase"

            if best_delta is not None and best_prob_after < base_prob - 0.02:
                # Convert scaled delta back to original units (approximate)
                original_delta = best_delta * std
                recommendations.append({
                    "action": f"{best_direction.capitalize()} {feat}",
                    "parameter": feat,
                    "direction": best_direction,
                    "predicted_probability_before": round(base_prob, 4),
                    "predicted_probability_after": round(best_prob_after, 4),
                    "probability_reduction": round(base_prob - best_prob_after, 4),
                    "basis": "what_if_model_inference",
                    "evidence": (
                        f"What-if inference: {best_direction} of {feat} reduces "
                        f"predicted defect probability from {base_prob:.1%} to {best_prob_after:.1%}"
                    ),
                    "uncertainty": "moderate",
                    "note": "What-if result from trained model. Not a certified process instruction.",
                })

        return sorted(recommendations, key=lambda x: x["probability_reduction"], reverse=True)

    except Exception as e:
        logger.warning(f"What-if inference failed: {e}")
        return []


def run(defect_output: dict) -> dict:
    """
    Main entry point for the Process Optimization Agent.

    Args:
        defect_output: dict from Defect Prediction Agent

    Returns:
        RecommendationOutput dict — stored in DB and displayed on dashboard.
    """
    record = defect_output.get("input_record", {})
    record_id = defect_output.get("record_id")
    risk_level = defect_output.get("risk_level", "UNKNOWN")
    prediction = defect_output.get("prediction", {})
    contributing_factors = defect_output.get("contributing_factors", [])
    rag_evidence = defect_output.get("rag_evidence", [])

    _load_artifacts()

    # Extract top features
    top_features = [f["feature"] for f in contributing_factors[:3]]
    violations = defect_output.get("anomaly_summary", {})
    stat_violations = []
    if defect_output.get("anomaly_summary"):
        # Re-retrieve from Quality Analysis output
        pass

    # Generate recommendations using multiple evidence bases
    all_recommendations = []

    # Approach (a): Rule-based
    rule_recs = _generate_rule_based_recommendations(record, stat_violations)
    all_recommendations.extend(rule_recs)

    # Approach (c): What-if inference
    if prediction.get("is_defective") or risk_level in ("HIGH", "ELEVATED"):
        whatif_recs = _generate_whatif_recommendations(record, top_features)
        all_recommendations.extend(whatif_recs)

    # De-duplicate by parameter
    seen_params = set()
    unique_recs = []
    for rec in all_recommendations:
        p = rec.get("parameter")
        if p and p not in seen_params:
            seen_params.add(p)
            unique_recs.append(rec)

    # If no evidence-based recommendations, explicitly say so
    if not unique_recs and risk_level in ("HIGH", "ELEVATED"):
        unique_recs.append({
            "action": "Manual inspection recommended",
            "parameter": None,
            "basis": "insufficient_model_evidence",
            "evidence": (
                "Defect risk is elevated but available model evidence is insufficient "
                "to generate a specific parameter adjustment recommendation. "
                "Manual inspection of top contributing factors is advised."
            ),
            "uncertainty": "high",
        })

    # RAG retrieval for recommendation context
    rec_rag_passages = []
    if top_features:
        query = f"corrective actions for {', '.join(top_features)} in manufacturing quality control"
        try:
            retrieve = _get_rag()
            rec_rag_passages = retrieve(query, top_k=2)
        except Exception as e:
            logger.warning(f"RAG retrieval for recommendations failed: {e}")

    # LLM synthesis (narration only — no invented numbers)
    recommendation_narrative = None
    if unique_recs:
        try:
            generate = _get_llm()
            llm_context = {
                "risk_level": risk_level,
                "predicted_probability": prediction.get("probability"),
                "recommendations": unique_recs[:3],
                "rag_context": rec_rag_passages[:2],
                "contributing_factors": contributing_factors[:3],
            }
            recommendation_narrative = generate(
                task="optimization_recommendation_narrative",
                context=llm_context,
                instruction=(
                    "Write a 2-3 sentence engineering recommendation summary. "
                    "Reference only the numerical values provided in the context. "
                    "Do not invent parameter values. "
                    "Use cautious language: 'may help reduce', 'is associated with', 'consider investigating'. "
                    "Reference the retrieved documentation if available. "
                    "End with: 'Human engineer review required before any process action.'"
                ),
            )
        except Exception as e:
            logger.warning(f"LLM recommendation narrative failed: {e}")

    output = {
        "agent": "process_optimization",
        "record_id": record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_level": risk_level,
        "recommendations": unique_recs,
        "recommendation_narrative": recommendation_narrative,
        "supporting_rag_evidence": rec_rag_passages,
        "contributing_factors": contributing_factors,
        "prediction_summary": prediction,
        "status": "AWAITING_HUMAN_REVIEW",  # Always requires human approval
        "human_in_the_loop": {
            "requires_approval": True,
            "approved_by": None,
            "approval_timestamp": None,
            "corrective_action_recorded": None,
        },
    }

    logger.info(
        f"[ProcessOptimization] Record {record_id}: "
        f"risk={risk_level}, "
        f"recommendations={len(unique_recs)}"
    )

    return output
