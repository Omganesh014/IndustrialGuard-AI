"""
backend/db/models.py

Database models for IndustrialGuard AI.

Uses SQLAlchemy ORM with SQLite (MVP).
Upgrade to PostgreSQL: change DATABASE_URL in .env -- ORM layer unchanged.

Tables:
- ProductionRecord: raw process parameter records
- Prediction: defect prediction results
- Anomaly: detected anomalies
- Recommendation: generated recommendations + human review status
- ModelVersion: model version registry
- PipelineRun: full agent pipeline execution log
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

# Database URL -- loaded from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./industrialguard.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call on application startup."""
    Base.metadata.create_all(bind=engine)


# ── Models ─────────────────────────────────────────────────────────────────────

class ProductionRecord(Base):
    __tablename__ = "production_records"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(64), unique=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    machine_id = Column(String(64), nullable=True)
    process_parameters = Column(JSON, nullable=False)   # raw {param: value} dict
    quality_status = Column(String(32), nullable=True)  # NORMAL / ABNORMAL / CRITICAL
    data_source_label = Column(String(64), default="UNKNOWN")  # provenance

    predictions = relationship("Prediction", back_populates="record")
    anomalies = relationship("Anomaly", back_populates="record")
    recommendations = relationship("Recommendation", back_populates="record")
    pipeline_runs = relationship("PipelineRun", back_populates="record")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(64), unique=True, index=True)
    record_id = Column(String(64), ForeignKey("production_records.record_id"), nullable=False)
    predicted_class = Column(String(32), nullable=False)   # DEFECTIVE / NORMAL / UNKNOWN
    probability = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True)
    model_version = Column(String(32), nullable=True)
    explanation = Column(JSON, nullable=True)  # SHAP / feature importance
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    record = relationship("ProductionRecord", back_populates="predictions")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(String(64), unique=True, index=True)
    record_id = Column(String(64), ForeignKey("production_records.record_id"), nullable=False)
    anomaly_type = Column(String(64), nullable=True)     # statistical / isolation_forest
    severity = Column(String(32), nullable=False)        # HIGH / MEDIUM / LOW / NORMAL
    affected_parameters = Column(JSON, nullable=True)    # list of {parameter, value, range}
    isolation_forest_score = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    record = relationship("ProductionRecord", back_populates="anomalies")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String(64), unique=True, index=True)
    record_id = Column(String(64), ForeignKey("production_records.record_id"), nullable=False)
    action = Column(Text, nullable=False)
    basis = Column(String(64), nullable=True)       # rule_based / historical / what_if_inference
    evidence = Column(Text, nullable=True)
    rag_source = Column(String(255), nullable=True)
    uncertainty = Column(String(32), nullable=True) # low / moderate / high
    status = Column(String(32), default="AWAITING_REVIEW")  # AWAITING_REVIEW / APPROVED / REJECTED
    approved_by = Column(String(64), nullable=True)
    approval_timestamp = Column(DateTime(timezone=True), nullable=True)
    corrective_action = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    record = relationship("ProductionRecord", back_populates="recommendations")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(32), unique=True, index=True)
    model_type = Column(String(64), nullable=False)
    training_date = Column(DateTime(timezone=True), nullable=True)
    dataset_version = Column(String(64), nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    train_metrics = Column(JSON, nullable=True)
    val_metrics = Column(JSON, nullable=True)
    test_metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True)
    record_id = Column(String(64), ForeignKey("production_records.record_id"), nullable=True)
    final_status = Column(String(32), nullable=True)
    final_risk_level = Column(String(32), nullable=True)
    agent_outputs = Column(JSON, nullable=True)  # full pipeline result
    error = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    record = relationship("ProductionRecord", back_populates="pipeline_runs")
