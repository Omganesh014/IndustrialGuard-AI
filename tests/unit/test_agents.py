"""
tests/unit/test_agents.py

Unit tests for the 4-agent pipeline architecture and orchestration.
"""

import pytest
from agents.monitoring.process_monitoring_agent import run as monitoring_run, validate_record
from agents.quality_analysis.quality_analysis_agent import run as quality_run
from agents.defect_prediction.defect_prediction_agent import run as defect_run
from agents.optimization.process_optimization_agent import run as optimization_run
from agents.orchestrator.pipeline import run_pipeline, run_demo_scenario


class TestProcessMonitoringAgent:
    def test_validate_record_valid(self):
        record = {
            "air_temperature": 300.0,
            "process_temperature": 310.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 50.0,
        }
        res = validate_record(record)
        assert res["is_valid"] is True
        assert len(res["missing_parameters"]) == 0
        assert len(res["range_violations"]) == 0

    def test_validate_record_out_of_physical_range(self):
        record = {
            "air_temperature": 150.0,  # below 250K minimum
            "process_temperature": 310.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 50.0,
        }
        res = validate_record(record)
        assert res["is_valid"] is False
        assert len(res["range_violations"]) > 0
        assert res["range_violations"][0]["parameter"] == "air_temperature"

    def test_monitoring_agent_normal_run(self):
        record = {
            "air_temperature": 300.0,
            "process_temperature": 310.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 20.0,
        }
        out = monitoring_run(record, record_id="REC_NORMAL_01")
        assert out["agent"] == "process_monitoring"
        assert out["process_status"] in ("NORMAL", "CAUTION")
        assert out["forward_to_quality_analysis"] is True


class TestQualityAnalysisAgent:
    def test_quality_analysis_rca(self):
        monitoring_out = {
            "input_record": {
                "air_temperature": 301.2,
                "process_temperature": 311.8,
                "rotational_speed": 1395.0,
                "torque": 65.0,
                "tool_wear": 220.0,
            },
            "record_id": "REC_ANOM_01",
            "anomaly_detection": {
                "is_anomaly": True,
                "severity": "HIGH",
                "statistical_violations": [
                    {"parameter": "tool_wear", "direction": "above", "deviation_iqr_units": 3.2},
                    {"parameter": "torque", "direction": "above", "deviation_iqr_units": 2.8},
                ],
            },
            "validation": {"is_valid": True, "missing_parameters": [], "range_violations": []},
        }
        out = quality_run(monitoring_out)
        assert out["agent"] == "quality_analysis"
        assert "contributing_factors" in out
        assert len(out["contributing_factors"]) > 0
        top_factor = out["contributing_factors"][0]["feature"]
        assert top_factor in ("tool_wear", "torque", "rotational_speed")


class TestPipelineOrchestrator:
    def test_run_pipeline_normal_batch(self):
        record = {
            "air_temperature": 300.0,
            "process_temperature": 310.0,
            "rotational_speed": 1500.0,
            "torque": 38.0,
            "tool_wear": 15.0,
        }
        res = run_pipeline(record, record_id="TEST_RUN_NORMAL")
        assert res["error"] is None
        assert res["final_status"] in ("NORMAL", "CAUTION")
        assert res["final_prediction"]["predicted_class"] == "NORMAL"

    def test_run_demo_scenario_executes_all_stages(self):
        res = run_demo_scenario()
        assert res["pipeline_run_id"] == "DEMO_BATCH_2024_001"
        assert "process_monitoring" in res["stages"]
        assert "quality_analysis" in res["stages"]
        assert "defect_prediction" in res["stages"]
        assert "process_optimization" in res["stages"]
        assert res["final_status"] in ("HIGH_RISK", "ELEVATED_RISK")
        assert res["final_risk_level"] in ("HIGH", "ELEVATED")
        assert len(res["final_recommendations"]) > 0
