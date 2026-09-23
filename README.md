# IndustrialGuard AI

**Agentic AI-Based Manufacturing Process Quality Control and Defect Prevention System**
*IBM Problem Statement #37 — Decision-Support Prototype*

---

## ⚠️ Important Disclaimer

This is a **decision-support prototype** built for research and demonstration purposes.

It does **NOT** claim:
- Certified industrial safety compliance
- Real factory deployment readiness
- Guaranteed defect prevention
- Guaranteed causal diagnosis of defects
- Autonomous machine control capability
- Replacement of qualified quality engineers

All data shown is labeled as: **REAL PUBLIC DATA**, **SYNTHETIC DATA**, **SIMULATED STREAM**, or **USER-PROVIDED DATA**.
"Continuous monitoring" in the demo = simulated streaming of historical/public data — never implied to be a live factory connection.

---

## System Overview

IndustrialGuard AI monitors manufacturing process parameters, detects anomalies, predicts potential defects, retrieves supporting technical knowledge, and presents evidence-grounded corrective recommendations — all reviewed and approved by a human engineer.

The core design principle is:

```
DATA → ML → DETECTION → PREDICTION → EXPLANATION → AGENT REASONING → RECOMMENDATION → HUMAN DECISION
```

This is NOT a `DATA → LLM → generic answer` system. ML/data-analysis components produce real evidence; the agentic layer interprets that evidence.

---

## Architecture

```
React Dashboard (Next.js)
        ↓
FastAPI (API gateway + DB access + ML inference)
        ↓
LangFlow (agent orchestration)
    ├── Process Monitoring Agent
    ├── Quality Analysis Agent
    ├── Defect Prediction Agent
    └── Process Optimization Agent
        ↓
    ML Modules          RAG / Vector Store       IBM Granite (watsonx.ai)
    (scikit-learn,      (ChromaDB embedded)      (narration, retrieval
     XGBoost, SHAP)                               synthesis, reports)
```

**Technology choices and their justifications are recorded in [`DECISION_LOG.md`](DECISION_LOG.md).**

---

## Repository Structure

```
industrialguard-ai/
├── data/
│   ├── raw/                  # Original unmodified dataset
│   ├── processed/            # Cleaned, feature-engineered data
│   ├── features/             # Feature definition files
│   └── synthetic/            # Project-generated demo data (labeled)
├── notebooks/                # EDA, model experiments, RAG evaluation
├── ml/
│   ├── preprocessing/        # Data cleaning, encoding, splitting
│   ├── models/               # Defect prediction models
│   ├── anomaly/              # Anomaly detection
│   ├── explainability/       # SHAP / feature importance
│   └── evaluation/           # Metrics, experiment results
├── agents/
│   ├── monitoring/           # Process Monitoring Agent
│   ├── quality_analysis/     # Quality Analysis Agent
│   ├── defect_prediction/    # Defect Prediction Agent
│   ├── optimization/         # Process Optimization Agent
│   └── orchestrator/         # Agent pipeline coordination
├── rag/
│   ├── ingestion/            # Document loading + chunking
│   ├── vectorstore/          # ChromaDB setup
│   ├── retrieval/            # Retrieval logic
│   └── knowledge_base/       # Source documents (labeled by tier)
├── backend/
│   ├── api/                  # FastAPI route handlers
│   ├── db/                   # Database models + migrations
│   └── services/             # Business logic layer
├── frontend/
│   ├── src/
│   │   ├── components/       # Dashboard UI components
│   │   ├── pages/            # Next.js pages
│   │   ├── hooks/            # Data fetching hooks
│   │   └── lib/              # API client, utilities
├── langflow/                 # LangFlow workflow definitions
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── ml/
│   └── rag/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── ml/
│   ├── agents/
│   └── rag/
├── scripts/                  # Setup, seeding, evaluation scripts
├── DECISION_LOG.md           # All major architecture/design decisions
├── DEMO_CONTRACT.md          # Fixed end-to-end demo workflow
├── DATASET.md                # Dataset documentation
├── .env.example              # Environment variable template
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- IBM Cloud account with watsonx.ai access (see Gate A in `DECISION_LOG.md`)
- LangFlow installed

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Fill in .env with your IBM credentials
uvicorn main:app --reload
```

### ML Pipeline

```bash
cd ml
python preprocessing/pipeline.py        # Preprocess dataset
python models/train.py                  # Train defect prediction model
python anomaly/detector.py              # Fit anomaly detector
python explainability/shap_analysis.py  # Generate SHAP values
```

### RAG Pipeline

```bash
cd rag
python ingestion/ingest.py              # Load and chunk documents
python vectorstore/setup.py             # Build ChromaDB index
python retrieval/test_retrieval.py      # Evaluate retrieval quality
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### LangFlow

```bash
langflow run
# Import workflow from langflow/industrialguard_workflow.json
```

---

## Data Sources

See [`DATASET.md`](DATASET.md) for full documentation.

All dataset statistics are real, sourced from the original dataset, and not fabricated.

---

## Scope Tiers

| Priority | Component |
|----------|-----------|
| 🔴 MUST | Dataset → preprocessing → anomaly detection → defect prediction → explainability → 4 agents → RAG consumed by agents → Granite reasoning → LangFlow workflow → dashboard (Overview/Monitoring/Prediction/Anomalies/Explainability/Recommendations) → polished demo |
| 🟡 SHOULD | Historical trends, alert thresholds, human approve/reject, multi-model comparison, SHAP |
| 🟢 NICE | Auth, rate limiting, model version registry, full test suite, real-time streaming, conversational assistant |

When cutting scope under time pressure: cut 🟢 → 🟡 → 🔴. Never trade a 🔴 for polish on lower tiers.

---

## Key Design Decisions

All decisions with their justifications are in [`DECISION_LOG.md`](DECISION_LOG.md).

This log is the authoritative record for "why did you choose X?" interview questions.

---

## Evaluation

See [`ml/evaluation/`](ml/evaluation/) for actual model metrics.

**No numbers are fabricated.** If a metric is not yet computed, it is listed as `[NOT YET EVALUATED]`.

---

## Limitations

- Trained on one publicly available dataset; generalization to other manufacturing processes is not validated.
- "Real-time" monitoring is simulated from historical data, not a live sensor feed.
- RAG knowledge base uses public/open-source documents; it does not contain proprietary manufacturing IP.
- LLM explanations are grounded in retrieved documents and model outputs, but are not certified engineering guidance.
- Anomaly thresholds are data-derived, not certified industrial safety thresholds.

---

## License

See `LICENSE`. Dataset licenses documented in `DATASET.md`.
