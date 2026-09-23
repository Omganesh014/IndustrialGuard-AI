"""
scripts/demo_run.py

Run the full demo scenario defined in DEMO_CONTRACT.md.
Tests the complete 4-agent pipeline with a real (SIMULATED STREAM) record.

Two records are tested:
1. A NORMAL record -- should produce no alerts
2. A HIGH-RISK record -- should produce DEFECTIVE prediction and recommendations

All data labeled as: SIMULATED STREAM (replayed from real dataset)
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator.pipeline import run_pipeline

# ── Record 1: Normal operation ─────────────────────────────────────────────────
# Values within normal operating ranges (from dataset normal-class median)
normal_record = {
    "air_temperature": 300.1,
    "process_temperature": 310.0,
    "rotational_speed": 1525.0,
    "torque": 39.2,
    "tool_wear": 110.0,
}

# ── Record 2: High-risk operation ─────────────────────────────────────────────
# High tool_wear + high torque + low rotational_speed = typical defect signature
# Based on dataset feature analysis (SHAP shows tool_wear and torque as top features)
high_risk_record = {
    "air_temperature": 304.8,
    "process_temperature": 315.2,
    "rotational_speed": 1180.0,
    "torque": 68.5,
    "tool_wear": 235.0,
}

def print_result(label, result):
    print(f"\n{'='*60}")
    print(f"DEMO RECORD: {label}")
    print(f"Data source: SIMULATED STREAM (replayed from CNC machining dataset)")
    print(f"{'='*60}")
    print(f"Process Status  : {result.get('final_status')}")
    print(f"Risk Level      : {result.get('final_risk_level')}")

    pred = result.get("final_prediction") or {}
    print(f"Prediction      : {pred.get('predicted_class')} "
          f"(prob={pred.get('probability')})")

    # Anomaly summary
    monitoring = result.get("stages", {}).get("process_monitoring", {})
    anomaly = monitoring.get("anomaly_detection", {})
    print(f"Anomaly Status  : {anomaly.get('status')} "
          f"(severity={anomaly.get('severity')})")
    if anomaly.get("statistical_violations"):
        print("  Violations:")
        for v in anomaly["statistical_violations"]:
            print(f"    - {v['parameter']}: {v['value']} "
                  f"({v['direction']} normal range, {v['deviation_iqr_units']} IQR units)")

    # Contributing factors
    qa = result.get("stages", {}).get("quality_analysis", {})
    factors = qa.get("contributing_factors", [])
    if factors:
        print("Contributing Factors (top 3):")
        for f in factors[:3]:
            print(f"    - {f['feature']} (relevance={f['relevance_score']})")
            for ev in f["evidence"][:1]:
                print(f"      Evidence type: {ev['type']}")

    # Recommendations
    recs = result.get("final_recommendations", [])
    if recs:
        print("Recommendations:")
        for r in recs[:2]:
            print(f"    - {r.get('action')}")
            print(f"      Basis: {r.get('basis')}")
            print(f"      Uncertainty: {r.get('uncertainty')}")

    if result.get("error"):
        print(f"[Pipeline error]: {result['error']}")

    print(f"\nNote: {pred.get('note', 'Requires human engineer review.')}")


if __name__ == "__main__":
    print("IndustrialGuard AI -- Demo Run")
    print("Data source label: SIMULATED STREAM")
    print("Not a live factory connection -- replaying historical CNC machining data\n")

    print("Running NORMAL record...")
    result_normal = run_pipeline(normal_record, record_id="DEMO_NORMAL_001")
    print_result("NORMAL OPERATION", result_normal)

    print("\nRunning HIGH-RISK record...")
    result_risk = run_pipeline(high_risk_record, record_id="DEMO_HIGH_RISK_001")
    print_result("HIGH-RISK OPERATION", result_risk)

    print("\n" + "="*60)
    print("Demo complete. See DEMO_CONTRACT.md for the full 9-step workflow.")
    print("Run the FastAPI backend + Next.js frontend for the full dashboard.")
