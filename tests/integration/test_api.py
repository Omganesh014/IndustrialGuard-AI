"""
tests/integration/test_api.py

Integration tests for the FastAPI backend.
Tests the API endpoints with a test database (in-memory SQLite).

Run: pytest tests/integration/ -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

import backend.db.models as db_models
from backend.db.models import Base, get_db
from backend.main import app

# ── Test database (file-based SQLite to survive lifespan init) ─────────────────
TEST_DB_URL = "sqlite:///./test_industrialguard.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    """
    Patch the models engine so lifespan init_db() creates tables on the test engine.
    Yield the TestClient, then drop all tables and clean up.
    """
    # Patch the engine used by init_db and get_db inside the models module
    with patch.object(db_models, "engine", test_engine), \
         patch.object(db_models, "SessionLocal", TestSessionLocal):
        Base.metadata.create_all(bind=test_engine)
        with TestClient(app) as c:
            yield c
        Base.metadata.drop_all(bind=test_engine)

    # Dispose engine connections before deleting the file (Windows file lock)
    import os
    test_engine.dispose()
    try:
        os.remove("test_industrialguard.db")
    except (FileNotFoundError, PermissionError):
        pass  # file lock on Windows — non-fatal, file will be overwritten next run


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Data ingestion ─────────────────────────────────────────────────────────────

def test_ingest_data_returns_record_id(client):
    r = client.post("/api/data", json={
        "parameters": {"feature_a": 50.0, "feature_b": 100.0},
        "data_source_label": "SYNTHETIC DATA",
    })
    assert r.status_code == 200
    body = r.json()
    assert "record_id" in body
    assert body["status"] == "stored"


def test_ingest_data_without_parameters_fails(client):
    r = client.post("/api/data", json={"data_source_label": "TEST"})
    # Missing 'parameters' field -- should return validation error
    assert r.status_code == 422


# ── Process Status ─────────────────────────────────────────────────────────────

def test_process_status_returns_list(client):
    r = client.get("/api/process-status")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Anomalies ──────────────────────────────────────────────────────────────────

def test_anomalies_returns_list(client):
    r = client.get("/api/anomalies")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Predictions ────────────────────────────────────────────────────────────────

def test_predictions_returns_list(client):
    r = client.get("/api/predictions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Recommendations ────────────────────────────────────────────────────────────

def test_recommendations_returns_list(client):
    r = client.get("/api/recommendations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_recommendation_review_not_found(client):
    r = client.post("/api/recommendations/nonexistent_id/review", json={
        "action": "APPROVED",
        "reviewer_id": "engineer_001",
    })
    assert r.status_code == 404


# ── Metrics ────────────────────────────────────────────────────────────────────

def test_metrics_returns_expected_fields(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "total_records" in body
    assert "anomaly_count" in body
    assert "defect_rate" in body
    assert "data_source_note" in body


# ── Full Pipeline Analysis ─────────────────────────────────────────────────────

def test_analyze_endpoint_runs_pipeline(client):
    r = client.post("/api/analyze", json={
        "parameters": {
            "air_temperature": 301.2,
            "process_temperature": 311.8,
            "rotational_speed": 1395.0,
            "torque": 64.5,
            "tool_wear": 218.0,
        },
        "machine_id": "CNC_01",
        "data_source_label": "SIMULATED STREAM",
    })
    assert r.status_code == 200
    data = r.json()
    assert "record_id" in data
    assert "final_status" in data
    assert "prediction" in data
    assert "recommendations_count" in data
    assert "pipeline_result" in data


# ── AI Chat Assistant ──────────────────────────────────────────────────────────

def test_chat_endpoint(client):
    r = client.post("/api/chat", json={
        "message": "What is the recommended tool wear operating threshold?"
    })
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert len(data["response"]) > 0
    assert "disclaimer" in data


# ── Model Performance ──────────────────────────────────────────────────────────

def test_model_performance_endpoint(client):
    r = client.get("/api/model-performance")
    assert r.status_code == 200
    data = r.json()
    assert "model_versions" in data
    assert len(data["model_versions"]) > 0
