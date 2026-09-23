"""
backend/main.py

FastAPI application entry point for IndustrialGuard AI.

API endpoints:
  POST /api/data              — ingest a new process record
  GET  /api/process-status    — latest process status
  GET  /api/anomalies         — recent anomalies
  GET  /api/predictions       — recent predictions
  GET  /api/recommendations   — recent recommendations (with human review actions)
  POST /api/analyze           — run full agent pipeline on a record
  POST /api/chat              — AI assistant (Granite + RAG)
  GET  /api/metrics           — overall quality metrics
  GET  /api/model-performance — model version + evaluation metrics
  POST /api/recommendations/{id}/review  — human approve/reject

Architecture separation:
- API layer: this file (routing, validation, HTTP)
- Service layer: backend/services/ (business logic)
- ML layer: ml/ modules (never called directly from routes)
- Agent layer: agents/ (called via services)
- DB layer: backend/db/ (ORM models + queries)
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.models import (
    Anomaly, ModelVersion, PipelineRun, Prediction,
    ProductionRecord, Recommendation, get_db, init_db,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Startup / Shutdown ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("IndustrialGuard AI starting up...")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("IndustrialGuard AI shutting down.")


app = FastAPI(
    title="IndustrialGuard AI",
    description=(
        "Agentic AI Manufacturing Quality Control System. "
        "Decision-support prototype — not a certified industrial control system."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend in development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────────────────

class ProcessRecord(BaseModel):
    """Incoming process parameter record."""
    record_id: str | None = Field(default=None, description="Optional client-provided ID")
    machine_id: str | None = Field(default=None)
    data_source_label: str = Field(default="USER-PROVIDED DATA")
    parameters: dict[str, float | str | int] = Field(
        ..., description="Process parameter values — keys must match trained feature names"
    )


class RecommendationReview(BaseModel):
    """Human engineer review of a recommendation."""
    action: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    reviewer_id: str = Field(..., min_length=1, max_length=64)
    corrective_action: str | None = Field(default=None)


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    record_id: str | None = Field(default=None, description="Optional: anchor context to a specific record")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "IndustrialGuard AI", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/data", summary="Ingest a new process record (without running full pipeline)")
def ingest_data(record: ProcessRecord, db: Session = Depends(get_db)):
    """Store a raw process record without running the agent pipeline."""
    record_id = record.record_id or f"rec_{uuid.uuid4().hex[:12]}"

    db_record = ProductionRecord(
        record_id=record_id,
        machine_id=record.machine_id,
        process_parameters=record.parameters,
        quality_status="PENDING",
        data_source_label=record.data_source_label,
    )
    db.add(db_record)
    db.commit()

    return {"record_id": record_id, "status": "stored", "message": "Use POST /api/analyze to run analysis."}


@app.post("/api/analyze", summary="Run full 4-agent pipeline on a process record")
def analyze_record(record: ProcessRecord, db: Session = Depends(get_db)):
    """
    Run the complete agent pipeline:
    Process Monitoring → Quality Analysis → Defect Prediction → Process Optimization

    Returns structured pipeline result including anomaly detection,
    defect prediction, contributing factors, and recommendations.
    """
    import time
    from agents.orchestrator.pipeline import run_pipeline

    record_id = record.record_id or f"rec_{uuid.uuid4().hex[:12]}"
    start_ms = time.time() * 1000

    # Run pipeline
    try:
        result = run_pipeline(record.parameters, record_id=record_id)
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    duration_ms = time.time() * 1000 - start_ms

    # Persist production record
    db_record = db.query(ProductionRecord).filter_by(record_id=record_id).first()
    if not db_record:
        db_record = ProductionRecord(
            record_id=record_id,
            machine_id=record.machine_id,
            process_parameters=record.parameters,
            quality_status=result.get("final_status"),
            data_source_label=record.data_source_label,
        )
        db.add(db_record)
    else:
        db_record.quality_status = result.get("final_status")

    # Persist prediction
    pred = result.get("final_prediction") or {}
    if pred.get("predicted_class"):
        db_pred = Prediction(
            prediction_id=f"pred_{uuid.uuid4().hex[:12]}",
            record_id=record_id,
            predicted_class=pred.get("predicted_class", "UNKNOWN"),
            probability=pred.get("probability"),
            risk_level=result.get("final_risk_level"),
            model_version=pred.get("model_version"),
            explanation=result.get("stages", {}).get("defect_prediction", {}).get("explanation"),
        )
        db.add(db_pred)

    # Persist anomaly
    anomaly_data = result.get("stages", {}).get("process_monitoring", {}).get("anomaly_detection", {})
    if anomaly_data.get("is_anomaly"):
        db_anomaly = Anomaly(
            anomaly_id=f"anom_{uuid.uuid4().hex[:12]}",
            record_id=record_id,
            anomaly_type="composite",
            severity=anomaly_data.get("severity", "UNKNOWN"),
            affected_parameters=anomaly_data.get("statistical_violations", []),
            isolation_forest_score=anomaly_data.get("isolation_forest_score"),
        )
        db.add(db_anomaly)

    # Persist recommendations
    for rec_item in result.get("final_recommendations", []):
        db_rec = Recommendation(
            recommendation_id=f"rec_{uuid.uuid4().hex[:12]}",
            record_id=record_id,
            action=rec_item.get("action", ""),
            basis=rec_item.get("basis"),
            evidence=rec_item.get("evidence"),
            rag_source=rec_item.get("rag_source"),
            uncertainty=rec_item.get("uncertainty"),
            status="AWAITING_REVIEW",
        )
        db.add(db_rec)

    # Persist pipeline run log
    db_run = PipelineRun(
        run_id=f"run_{uuid.uuid4().hex[:12]}",
        record_id=record_id,
        final_status=result.get("final_status"),
        final_risk_level=result.get("final_risk_level"),
        agent_outputs=result.get("stages"),
        error=result.get("error"),
        duration_ms=round(duration_ms, 2),
    )
    db.add(db_run)
    db.commit()

    return {
        "record_id": record_id,
        "final_status": result.get("final_status"),
        "final_risk_level": result.get("final_risk_level"),
        "prediction": result.get("final_prediction"),
        "recommendations_count": len(result.get("final_recommendations", [])),
        "pipeline_result": result,
        "duration_ms": round(duration_ms, 2),
        "disclaimer": "Decision-support output. Requires human engineer review.",
    }


@app.get("/api/process-status", summary="Latest process status")
def get_process_status(limit: int = 20, db: Session = Depends(get_db)):
    records = (
        db.query(ProductionRecord)
        .order_by(ProductionRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "record_id": r.record_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "machine_id": r.machine_id,
            "quality_status": r.quality_status,
            "data_source_label": r.data_source_label,
        }
        for r in records
    ]


@app.get("/api/anomalies", summary="Recent anomalies")
def get_anomalies(limit: int = 50, db: Session = Depends(get_db)):
    anomalies = (
        db.query(Anomaly)
        .order_by(Anomaly.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "anomaly_id": a.anomaly_id,
            "record_id": a.record_id,
            "severity": a.severity,
            "anomaly_type": a.anomaly_type,
            "affected_parameters": a.affected_parameters,
            "isolation_forest_score": a.isolation_forest_score,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
        }
        for a in anomalies
    ]


@app.get("/api/predictions", summary="Recent defect predictions")
def get_predictions(limit: int = 50, db: Session = Depends(get_db)):
    preds = (
        db.query(Prediction)
        .order_by(Prediction.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "prediction_id": p.prediction_id,
            "record_id": p.record_id,
            "predicted_class": p.predicted_class,
            "probability": p.probability,
            "risk_level": p.risk_level,
            "model_version": p.model_version,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
        }
        for p in preds
    ]


@app.get("/api/recommendations", summary="Recent recommendations (awaiting review)")
def get_recommendations(
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Recommendation)
    if status:
        query = query.filter(Recommendation.status == status)
    recs = query.order_by(Recommendation.timestamp.desc()).limit(limit).all()
    return [
        {
            "recommendation_id": r.recommendation_id,
            "record_id": r.record_id,
            "action": r.action,
            "basis": r.basis,
            "evidence": r.evidence,
            "rag_source": r.rag_source,
            "uncertainty": r.uncertainty,
            "status": r.status,
            "approved_by": r.approved_by,
            "approval_timestamp": r.approval_timestamp.isoformat() if r.approval_timestamp else None,
            "corrective_action": r.corrective_action,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in recs
    ]


@app.post("/api/recommendations/{recommendation_id}/review", summary="Human review of a recommendation")
def review_recommendation(
    recommendation_id: str,
    review: RecommendationReview,
    db: Session = Depends(get_db),
):
    """
    Human-in-the-loop: approve or reject a recommendation.
    Records the reviewer, decision, and any corrective action taken.
    """
    rec = db.query(Recommendation).filter_by(recommendation_id=recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "AWAITING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Recommendation already reviewed: {rec.status}")

    rec.status = review.action
    rec.approved_by = review.reviewer_id
    rec.approval_timestamp = datetime.now(timezone.utc)
    rec.corrective_action = review.corrective_action
    db.commit()

    return {
        "recommendation_id": recommendation_id,
        "status": rec.status,
        "approved_by": rec.approved_by,
        "message": "Review recorded. This is a decision-support action — not automated machine control.",
    }


@app.get("/api/metrics", summary="Overall quality metrics")
def get_metrics(hours: int = 24, db: Session = Depends(get_db)):
    """Aggregate quality metrics for the dashboard overview."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    total_records = db.query(ProductionRecord).filter(ProductionRecord.timestamp >= since).count()
    anomaly_count = db.query(Anomaly).filter(Anomaly.timestamp >= since).count()
    high_anomalies = db.query(Anomaly).filter(Anomaly.timestamp >= since, Anomaly.severity == "HIGH").count()
    defective_preds = db.query(Prediction).filter(
        Prediction.timestamp >= since, Prediction.predicted_class == "DEFECTIVE"
    ).count()
    total_preds = db.query(Prediction).filter(Prediction.timestamp >= since).count()
    pending_recs = db.query(Recommendation).filter(Recommendation.status == "AWAITING_REVIEW").count()

    return {
        "period_hours": hours,
        "total_records": total_records,
        "anomaly_count": anomaly_count,
        "high_severity_anomalies": high_anomalies,
        "predicted_defective": defective_preds,
        "total_predictions": total_preds,
        "defect_rate": round(defective_preds / max(total_preds, 1), 4),
        "pending_recommendations": pending_recs,
        "data_source_note": "Metrics computed from stored prediction records — not fabricated.",
    }


@app.get("/api/model-performance", summary="Model version and evaluation metrics")
def get_model_performance(db: Session = Depends(get_db)):
    """Return stored model version metadata and evaluation metrics."""
    import json
    from pathlib import Path

    versions = []
    eval_dir = Path("ml/evaluation")
    for f in sorted(eval_dir.glob("model_version_*.json")):
        with open(f) as fp:
            versions.append(json.load(fp))

    return {
        "model_versions": versions,
        "note": "Metrics from actual model evaluation — not fabricated. See ml/evaluation/ for full results.",
    }


@app.post("/api/chat", summary="AI assistant — grounded in current data and RAG knowledge")
def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """
    Conversational interface.
    Granite generates answers grounded in:
    - Available DB records (for context on specific record_id)
    - RAG knowledge base
    - Explicit system instructions (no hallucination)
    """
    from backend.services.granite_client import generate_narrative
    from rag.retrieval.retriever import retrieve

    # Build context from DB if record_id provided
    context: dict = {"question": message.message}

    if message.record_id:
        pred = db.query(Prediction).filter_by(record_id=message.record_id).first()
        anom = db.query(Anomaly).filter_by(record_id=message.record_id).first()
        recs = db.query(Recommendation).filter_by(record_id=message.record_id).all()
        context["record_id"] = message.record_id
        if pred:
            context["prediction"] = {
                "class": pred.predicted_class,
                "probability": pred.probability,
                "risk_level": pred.risk_level,
                "explanation": pred.explanation,
            }
        if anom:
            context["anomaly"] = {
                "severity": anom.severity,
                "affected_parameters": anom.affected_parameters,
            }
        if recs:
            context["recommendations"] = [
                {"action": r.action, "basis": r.basis, "status": r.status}
                for r in recs
            ]

    # RAG retrieval for the question
    try:
        rag_passages = retrieve(message.message, top_k=3)
        context["retrieved_knowledge"] = [
            {"content": p["content"][:300], "source": p["source"], "tier": p["tier_label"]}
            for p in rag_passages
        ]
    except Exception as e:
        logger.warning(f"RAG retrieval failed for chat: {e}")

    response = generate_narrative(task="chat_assistant", context=context)

    return {
        "response": response,
        "rag_sources": [p["source"] for p in (context.get("retrieved_knowledge") or [])],
        "disclaimer": "AI-generated response grounded in available data. Not certified engineering advice.",
    }
