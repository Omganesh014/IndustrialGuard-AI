"""
tests/ml/test_models.py

Unit and integration tests for ML model inference and SHAP explainability.
"""

import pytest
import numpy as np
import pandas as pd
from ml.models.inference import predict, batch_predict
from ml.explainability.shap_analysis import compute_global_importance, explain_single_prediction
import joblib
from pathlib import Path


class TestModelInference:
    def test_predict_returns_valid_structure(self):
        sample = {
            "air_temperature": 300.5,
            "process_temperature": 310.2,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 50.0,
        }
        res = predict(sample)
        assert "prediction" in res
        assert res["prediction"] in ("NORMAL", "DEFECTIVE")
        assert "probability" in res
        assert 0.0 <= res["probability"] <= 1.0
        assert res["model_version"] == "v1.0"
        assert "data_source_label" in res

    def test_predict_high_defect_sample(self):
        defective_sample = {
            "air_temperature": 301.2,
            "process_temperature": 311.8,
            "rotational_speed": 1395.0,
            "torque": 65.0,
            "tool_wear": 220.0,
        }
        res = predict(defective_sample)
        assert res["prediction"] == "DEFECTIVE"
        assert res["probability"] > 0.5

    def test_batch_predict(self):
        samples = [
            {"air_temperature": 300.0, "process_temperature": 310.0, "rotational_speed": 1500.0, "torque": 35.0, "tool_wear": 20.0},
            {"air_temperature": 302.0, "process_temperature": 312.0, "rotational_speed": 1350.0, "torque": 68.0, "tool_wear": 230.0},
        ]
        results = batch_predict(samples)
        assert len(results) == 2
        assert results[0]["prediction"] == "NORMAL"
        assert results[1]["prediction"] == "DEFECTIVE"


class TestExplainability:
    def test_explain_single_prediction(self):
        model = joblib.load(Path("ml/models/defect_predictor_v1.0.pkl"))
        scaler = joblib.load(Path("ml/models/artifacts/scaler.pkl"))
        feature_cols = ["air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear"]

        sample = {
            "air_temperature": 301.2,
            "process_temperature": 311.8,
            "rotational_speed": 1395.0,
            "torque": 65.0,
            "tool_wear": 220.0,
        }
        explanation = explain_single_prediction(model, sample, feature_cols, scaler)
        assert "explanation_method" in explanation
        assert "local_contributions" in explanation
        assert len(explanation["local_contributions"]) > 0
