"""
agents/orchestrator/pipeline.py

Agent Pipeline Orchestrator for IndustrialGuard AI.

Coordinates the 4-agent pipeline:
    Process Monitoring → Quality Analysis → Defect Prediction → Process Optimization

Uses structured JSON passing between agents -- never free text.
Each agent's output is validated before forwarding downstream.
Errors in any agent are caught, logged, and handled gracefully (partial output preserved).

This module is called by:
- FastAPI backend (/api/analyze endpoint)
- LangFlow workflow (trigger node)
- Test suite
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def run_pipeline(record: dict, record_id: str | None = None) -> dict:
    """
    Execute the full 4-agent pipeline on a single process record.

    Args:
        record:    dict of {parameter_name: value}
        record_id: optional identifier string

    Returns:
        PipelineResult dict containing outputs from all agents and final recommendation.
        Partial results are preserved if an agent fails.
    """
    if record_id is None:
        record_id = f"rec_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"

    pipeline_result = {
        "pipeline_run_id": record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_record": record,
        "stages": {},
        "final_status": None,
        "final_risk_level": None,
        "error": None,
    }

    # ── Stage 1: Process Monitoring ────────────────────────────────────────────
    try:
        from agents.monitoring.process_monitoring_agent import run as monitoring_run
        monitoring_output = monitoring_run(record, record_id=record_id)
        pipeline_result["stages"]["process_monitoring"] = monitoring_output
        logger.info(f"[Pipeline] Stage 1 complete: status={monitoring_output.get('process_status')}")
    except Exception as e:
        logger.error(f"[Pipeline] Stage 1 (Process Monitoring) failed: {e}")
        pipeline_result["stages"]["process_monitoring"] = {"error": str(e)}
        pipeline_result["error"] = f"Process monitoring failed: {e}"
        pipeline_result["final_status"] = "PIPELINE_ERROR"
        return pipeline_result

    # ── Stage 2: Quality Analysis ──────────────────────────────────────────────
    try:
        from agents.quality_analysis.quality_analysis_agent import run as quality_run
        quality_output = quality_run(monitoring_output)
        pipeline_result["stages"]["quality_analysis"] = quality_output
        logger.info(
            f"[Pipeline] Stage 2 complete: "
            f"anomaly={quality_output.get('anomaly_summary', {}).get('is_anomaly')}, "
            f"factors={len(quality_output.get('contributing_factors', []))}"
        )
    except Exception as e:
        logger.error(f"[Pipeline] Stage 2 (Quality Analysis) failed: {e}")
        pipeline_result["stages"]["quality_analysis"] = {"error": str(e)}
        # Continue pipeline with degraded output
        quality_output = {
            "input_record": record,
            "record_id": record_id,
            "timestamp": monitoring_output.get("timestamp"),
            "process_status": monitoring_output.get("process_status"),
            "anomaly_summary": monitoring_output.get("anomaly_detection", {}),
            "contributing_factors": [],
            "rag_evidence": [],
            "llm_narrative": None,
        }

    # ── Stage 3: Defect Prediction ─────────────────────────────────────────────
    try:
        from agents.defect_prediction.defect_prediction_agent import run as prediction_run
        defect_output = prediction_run(quality_output)
        pipeline_result["stages"]["defect_prediction"] = defect_output
        logger.info(
            f"[Pipeline] Stage 3 complete: "
            f"prediction={defect_output.get('prediction', {}).get('predicted_class')}, "
            f"probability={defect_output.get('prediction', {}).get('probability')}, "
            f"risk={defect_output.get('risk_level')}"
        )
    except Exception as e:
        logger.error(f"[Pipeline] Stage 3 (Defect Prediction) failed: {e}")
        pipeline_result["stages"]["defect_prediction"] = {"error": str(e)}
        defect_output = {
            "input_record": record,
            "record_id": record_id,
            "prediction": {"predicted_class": "UNKNOWN", "probability": None, "is_defective": None},
            "risk_level": "UNKNOWN",
            "contributing_factors": quality_output.get("contributing_factors", []),
            "rag_evidence": quality_output.get("rag_evidence", []),
            "anomaly_summary": quality_output.get("anomaly_summary"),
        }

    # ── Stage 4: Process Optimization ─────────────────────────────────────────
    try:
        from agents.optimization.process_optimization_agent import run as optimization_run
        optimization_output = optimization_run(defect_output)
        pipeline_result["stages"]["process_optimization"] = optimization_output
        logger.info(
            f"[Pipeline] Stage 4 complete: "
            f"recommendations={len(optimization_output.get('recommendations', []))}"
        )
    except Exception as e:
        logger.error(f"[Pipeline] Stage 4 (Process Optimization) failed: {e}")
        pipeline_result["stages"]["process_optimization"] = {"error": str(e)}
        optimization_output = {
            "recommendations": [],
            "risk_level": defect_output.get("risk_level", "UNKNOWN"),
        }

    # ── Final Summary ──────────────────────────────────────────────────────────
    pipeline_result["final_status"] = monitoring_output.get("process_status", "UNKNOWN")
    pipeline_result["final_risk_level"] = defect_output.get("risk_level", "UNKNOWN")
    pipeline_result["final_prediction"] = defect_output.get("prediction")
    pipeline_result["final_recommendations"] = optimization_output.get("recommendations", [])
    pipeline_result["final_recommendation_narrative"] = optimization_output.get("recommendation_narrative")

    logger.info(
        f"[Pipeline] Complete -- "
        f"run_id={record_id}, "
        f"status={pipeline_result['final_status']}, "
        f"risk={pipeline_result['final_risk_level']}"
    )

    return pipeline_result


def run_demo_scenario(record: dict | None = None) -> dict:
    """
    Run the fixed demo scenario defined in DEMO_CONTRACT.md.
    Demonstrates Batch 2024-001 Incident:
    - Tool wear > 200 min
    - Elevated cutting torque
    - High defect probability & anomaly severity
    """
    demo_record = record or {
        "air_temperature": 301.2,
        "process_temperature": 311.8,
        "rotational_speed": 1395.0,
        "torque": 64.5,
        "tool_wear": 218.0,
        "_data_source": "SIMULATED STREAM -- DEMO INCIDENT",
    }
    logger.info("[Demo] Running demo scenario -- SIMULATED STREAM")
    return run_pipeline(demo_record, record_id="DEMO_BATCH_2024_001")
