"""
agents/monitoring/process_monitoring_agent.py

Process Monitoring Agent -- Agent 1 of 4

Responsibilities:
- Accept incoming process records (single or batch)
- Validate data completeness and range
- Run anomaly detection
- Flag deviations from normal operating conditions
- Produce structured output for downstream agents (Quality Analysis Agent)
- Never perform LLM-based decisions here -- only deterministic validation + ML anomaly detection

Input:  dict of {parameter: value} -- raw process parameters
Output: ProcessMonitoringOutput (structured dict / JSON)

The agent does NOT call the LLM. It calls the ML anomaly detector.
LLM reasoning happens downstream in the Quality Analysis Agent.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import to avoid loading ML artifacts at module import time
_anomaly_detector = None


def _get_detector():
    global _anomaly_detector
    if _anomaly_detector is None:
        from ml.anomaly.detector import detect_anomalies
        _anomaly_detector = detect_anomalies
    return _anomaly_detector


# ── Expected parameter schema ──────────────────────────────────────────────────
# Fill this after Gate B dataset inspection.
# Maps parameter names to (min_valid, max_valid) for hard-limit validation.
# These are PHYSICAL VALIDITY ranges (e.g., temperature can't be -500°C),
# NOT defect thresholds -- those come from the trained anomaly detector.
PARAMETER_SCHEMA: dict[str, dict[str, Any]] = {
    "air_temperature":     {"min": 250.0, "max": 350.0, "unit": "K"},
    "process_temperature": {"min": 250.0, "max": 400.0, "unit": "K"},
    "rotational_speed":    {"min": 500.0, "max": 5000.0, "unit": "rpm"},
    "torque":              {"min": 0.0,   "max": 200.0, "unit": "Nm"},
    "tool_wear":           {"min": 0.0,   "max": 500.0, "unit": "min"},
    "temperature":         {"min": -50.0, "max": 1000.0, "unit": "°C"},
    "pressure":            {"min": 0.0,   "max": 1000.0, "unit": "bar"},
    "vibration":           {"min": 0.0,   "max": 100.0, "unit": "mm/s"},
}

REQUIRED_PARAMETERS: list[str] = []


def _get_required_parameters() -> list[str]:
    global REQUIRED_PARAMETERS
    if not REQUIRED_PARAMETERS:
        feat_path = Path("data/features/feature_columns.json")
        if feat_path.exists():
            try:
                with open(feat_path) as f:
                    REQUIRED_PARAMETERS = json.load(f).get("features", [])
            except Exception:
                pass
    return REQUIRED_PARAMETERS


def validate_record(record: dict) -> dict:
    """
    Validate a single process record for:
    1. Missing required parameters
    2. Physical validity range violations
    3. Data type correctness

    Returns validation_result dict.
    """
    req_params = _get_required_parameters()
    missing = [p for p in req_params if p not in record or record[p] is None]
    range_violations = []

    for param, constraints in PARAMETER_SCHEMA.items():
        if param not in record:
            continue
        try:
            val = float(record[param])
        except (TypeError, ValueError):
            range_violations.append({
                "parameter": param,
                "issue": "non_numeric_value",
                "value": record[param],
            })
            continue

        if val < constraints["min"] or val > constraints["max"]:
            range_violations.append({
                "parameter": param,
                "issue": "outside_physical_range",
                "value": val,
                "valid_range": [constraints["min"], constraints["max"]],
                "unit": constraints.get("unit", ""),
            })

    is_valid = len(missing) == 0 and len(range_violations) == 0

    return {
        "is_valid": is_valid,
        "missing_parameters": missing,
        "range_violations": range_violations,
        "completeness_score": round(
            1.0 - len(missing) / max(len(REQUIRED_PARAMETERS), 1), 4
        ),
    }


def run(record: dict, record_id: str | None = None) -> dict:
    """
    Main entry point for the Process Monitoring Agent.

    Args:
        record:    dict of {parameter_name: value} -- one process record
        record_id: optional identifier for the record

    Returns:
        Structured ProcessMonitoringOutput dict -- consumed by Quality Analysis Agent.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Validate
    validation = validate_record(record)

    if not validation["is_valid"]:
        logger.warning(
            f"Record {record_id}: validation failed -- "
            f"missing={validation['missing_parameters']}, "
            f"violations={validation['range_violations']}"
        )

    # Step 2: Anomaly detection (runs regardless of minor validation issues)
    try:
        detect = _get_detector()
        anomaly_result = detect(record)
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        anomaly_result = {
            "status": "ERROR",
            "error": str(e),
            "is_anomaly": None,
            "severity": "UNKNOWN",
        }

    # Step 3: Build structured output
    output = {
        "agent": "process_monitoring",
        "record_id": record_id,
        "timestamp": timestamp,
        "input_record": record,
        "validation": validation,
        "anomaly_detection": anomaly_result,
        "process_status": _determine_process_status(validation, anomaly_result),
        "forward_to_quality_analysis": True,  # always forward; Quality Analysis Agent decides depth
        "data_source_label": "SIMULATED STREAM",  # update at runtime if live or user-provided
    }

    logger.info(
        f"[ProcessMonitoring] Record {record_id}: "
        f"status={output['process_status']}, "
        f"anomaly={anomaly_result.get('is_anomaly')}, "
        f"severity={anomaly_result.get('severity')}"
    )

    return output


def _determine_process_status(validation: dict, anomaly: dict) -> str:
    """Derive a single process status label from validation and anomaly outputs."""
    if not validation["is_valid"] and anomaly.get("severity") == "HIGH":
        return "CRITICAL"
    if anomaly.get("severity") == "HIGH":
        return "HIGH_RISK"
    if anomaly.get("severity") == "MEDIUM":
        return "ELEVATED_RISK"
    if anomaly.get("severity") == "LOW" or not validation["is_valid"]:
        return "CAUTION"
    if anomaly.get("status") == "NORMAL":
        return "NORMAL"
    return "UNKNOWN"
