"""
agents/quality_analysis/quality_analysis_agent.py

Quality Analysis Agent — Agent 2 of 4

Responsibilities:
- Receive structured output from Process Monitoring Agent
- Perform statistical analysis of deviations
- Correlate anomaly findings with historical patterns
- Trigger Root-Cause Analysis (RCA is a CAPABILITY of this agent, not a 5th agent)
- Retrieve supporting evidence from RAG knowledge base
- Produce structured quality assessment for Defect Prediction Agent
- Call Granite/LLM only for NARRATION of analysis results — never for numerical analysis

Input:  ProcessMonitoringOutput dict (from Agent 1)
Output: QualityAnalysisOutput dict (consumed by Agent 3)

RCA Logic:
  1. Get top features from anomaly statistical violations
  2. Get global feature importance from explainability module
  3. Retrieve RAG passages relevant to top features
  4. Combine into contributing_factors list with evidence tags
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EVAL_DIR = Path("ml/evaluation")

# Lazy imports
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


def _load_global_importance() -> list[dict]:
    """Load pre-computed global feature importance."""
    imp_path = EVAL_DIR / "global_feature_importance.json"
    if imp_path.exists():
        with open(imp_path) as f:
            return json.load(f)
    logger.warning("Global feature importance not found. Run ml/explainability/shap_analysis.py.")
    return []


def _build_rca(
    statistical_violations: list[dict],
    global_importance: list[dict],
    rag_passages: list[dict],
) -> list[dict]:
    """
    Root-Cause Analysis — a capability of the Quality Analysis Agent.

    Combines:
    1. Statistical violations from the anomaly detector (observed deviations)
    2. Global feature importance (model-derived importance ranking)
    3. RAG evidence (retrieved documentation supporting the factor)

    Returns a list of contributing factors with evidence tags.
    Language uses "associated with" / "likely contributing" — never claims causation.
    """
    # Map violation parameters for quick lookup
    violation_map = {v["parameter"]: v for v in statistical_violations}

    # Map importance for quick lookup
    importance_map = {item["feature"]: item["importance"] for item in global_importance}

    # Collect all candidate factors
    candidate_features = set(list(violation_map.keys()) + [i["feature"] for i in global_importance[:10]])

    factors = []
    for feat in candidate_features:
        evidence_tags = []
        stat_evidence = violation_map.get(feat)
        model_importance = importance_map.get(feat)

        if stat_evidence:
            evidence_tags.append({
                "type": "statistical_violation",
                "detail": (
                    f"{feat} is {stat_evidence['direction']} normal range "
                    f"(deviation: {stat_evidence['deviation_iqr_units']:.1f} IQR units)"
                ),
            })
        if model_importance and model_importance > 0:
            evidence_tags.append({
                "type": "model_feature_importance",
                "detail": f"Model assigns importance score {model_importance:.4f} to {feat}",
            })

        # Match RAG passages
        for passage in rag_passages:
            if feat.lower().replace("_", " ") in passage.get("content", "").lower():
                evidence_tags.append({
                    "type": "rag_retrieved_documentation",
                    "source": passage.get("source", "unknown"),
                    "tier": passage.get("tier", "unknown"),
                    "excerpt": passage.get("content", "")[:200],
                })

        if evidence_tags:
            # Composite relevance score: presence in both violation + model importance
            relevance = (1 if stat_evidence else 0) + (model_importance or 0)
            factors.append({
                "feature": feat,
                "relevance_score": round(relevance, 4),
                "evidence": evidence_tags,
                "language_note": (
                    "This feature is associated with elevated defect risk. "
                    "This does not imply causation."
                ),
            })

    # Sort by relevance
    factors.sort(key=lambda x: x["relevance_score"], reverse=True)
    return factors[:5]  # Top 5 contributing factors


def run(monitoring_output: dict) -> dict:
    """
    Main entry point for the Quality Analysis Agent.

    Args:
        monitoring_output: dict from Process Monitoring Agent

    Returns:
        QualityAnalysisOutput dict consumed by Defect Prediction Agent.
    """
    record = monitoring_output.get("input_record", {})
    anomaly = monitoring_output.get("anomaly_detection", {})
    validation = monitoring_output.get("validation", {})

    # Step 1: Load global importance
    global_importance = _load_global_importance()

    # Step 2: Build RAG query from top violated / important parameters
    top_features = [v["parameter"] for v in anomaly.get("statistical_violations", [])][:3]
    if not top_features and global_importance:
        top_features = [item["feature"] for item in global_importance[:3]]

    # Step 3: RAG retrieval
    rag_passages = []
    if top_features:
        query = f"manufacturing quality issues related to {', '.join(top_features)}"
        try:
            retrieve = _get_rag()
            rag_passages = retrieve(query, top_k=3)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}. Proceeding without retrieved context.")

    # Step 4: Root-Cause Analysis
    contributing_factors = _build_rca(
        statistical_violations=anomaly.get("statistical_violations", []),
        global_importance=global_importance,
        rag_passages=rag_passages,
    )

    # Step 5: Statistical deviation summary
    violations = anomaly.get("statistical_violations", [])
    high_deviation_params = [
        v["parameter"] for v in violations if v.get("deviation_iqr_units", 0) > 2.0
    ]

    # Step 6: LLM narration (ONLY for human-readable text — no numerical work)
    narrative = None
    if anomaly.get("is_anomaly"):
        try:
            generate = _get_llm()
            llm_context = {
                "process_status": monitoring_output.get("process_status"),
                "anomaly_severity": anomaly.get("severity"),
                "contributing_factors": contributing_factors[:3],
                "rag_passages": rag_passages[:2],
            }
            narrative = generate(
                task="quality_analysis_narration",
                context=llm_context,
                instruction=(
                    "Briefly narrate the quality analysis findings in 2-3 sentences. "
                    "Use language like 'associated with' and 'likely contributing factor'. "
                    "Do not invent numerical values. Do not claim causation. "
                    "Reference the retrieved documentation if available."
                ),
            )
        except Exception as e:
            logger.warning(f"LLM narration failed: {e}. Narrative will be omitted.")

    output = {
        "agent": "quality_analysis",
        "record_id": monitoring_output.get("record_id"),
        "timestamp": monitoring_output.get("timestamp"),
        "process_status": monitoring_output.get("process_status"),
        "anomaly_summary": {
            "is_anomaly": anomaly.get("is_anomaly"),
            "severity": anomaly.get("severity"),
            "violation_count": anomaly.get("violation_count", 0),
            "high_deviation_parameters": high_deviation_params,
        },
        "contributing_factors": contributing_factors,
        "rag_evidence": rag_passages,
        "llm_narrative": narrative,
        "forward_to_defect_prediction": True,
        "input_record": record,
        "validation_summary": validation,
    }

    logger.info(
        f"[QualityAnalysis] Record {monitoring_output.get('record_id')}: "
        f"anomaly={anomaly.get('is_anomaly')}, "
        f"contributing_factors={len(contributing_factors)}, "
        f"rag_passages={len(rag_passages)}"
    )

    return output
