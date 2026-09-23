# IndustrialGuard AI — Decision Log

This log records every major architecture, dataset, model, and design decision.
It is the authoritative source for justifying choices during code review, viva, or technical interviews.

**Rule:** Every decision here is traceable to evidence — benchmark results, gate checks, or documented constraints.
No decision reads "because it is popular" without a supporting technical reason.

---

## Decision Record Format

```
DECISION-NNN
Date: YYYY-MM-DD
Status: PROPOSED | ACCEPTED | SUPERSEDED
Category: Dataset | Architecture | ML | RAG | Agent | Infrastructure
Decision: [What was decided]
Alternatives considered: [What else was evaluated]
Justification: [Why this choice, with evidence or constraint]
Superseded by: [if applicable]
```

---

## Gate Decisions

### DECISION-001
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Architecture  
**Decision:** IBM watsonx.ai (Granite-13b-instruct-v2) + Embedded Fast Fallback  
**Alternatives considered:**  
- Option B: IBM Cloud Agentic Lab + Granite
- Option C: LangChain + RAG + Granite standalone  
**Justification:** Watsonx.ai provides certified enterprise foundation models. To guarantee high demo reliability and CI resilience, an embedded caching layer (`USE_CACHED_GRANITE_RESPONSES`) was added, ensuring deterministic narration when IBM cloud credentials are absent or during connectivity drops.

---

### DECISION-002
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Dataset  
**Decision:** AI4I 2020 Predictive Maintenance Manufacturing Dataset  
**Alternatives considered:**  

| Criterion | AI4I 2020 (Selected) | CNC Milling Tool Wear | SECOM Semiconductor |
|-----------|----------------------|-----------------------|---------------------|
| Manufacturing realism (3×) | 9 (physical equations) | 8 (real CNC) | 7 (high dimensionality) |
| Defect/quality label present (3×) | 9 (binary & mode flags) | 7 (tool condition) | 6 (extreme imbalance) |
| Sample count (2×) | 9 (2,000+ records) | 6 (18 runs) | 7 (1,567 records) |
| Feature richness (2×) | 9 (temperatures, speed, torque, wear) | 8 (vibration, acoustic) | 6 (590 unnamed sensors) |
| Supports anomaly detection (2×) | 9 (clear normal vs abnormal envelope) | 8 (wear progression) | 6 (high noise) |
| Supports supervised prediction (2×) | 9 (failure modes defined) | 7 (regression to life) | 6 (sparse positive class) |
| License permits this use (3×) | 9 (CC BY 4.0 / Public) | 8 (Open access) | 8 (Public domain) |
| Demo-friendliness (1×) | 9 (interpretable physical units) | 7 (large raw time-series) | 5 (abstract sensor IDs) |
| **WEIGHTED TOTAL** | **153** | **130** | **111** |

**Justification:** The AI4I 2020 dataset models real-world physical failure modes (Heat Dissipation, Power, Overstrain, Tool Wear Failure) with direct physical interpretability.

---

### DECISION-003
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** RAG  
**Decision:** 3-Tier Hierarchical Knowledge Base  
**Alternatives considered:** Single flat document pool, ungrounded LLM prompting  
**Justification:** Clear provenance prevents hallucination and establishes evidentiary hierarchy.  
**Tier classification:**  
- **Tier 1 (Public International Standards):** `iso_13374_condition_monitoring.md` (Condition monitoring and machine diagnostics information architecture).  
- **Tier 2 (Industrial Technical Manuals):** `tool_wear_thermal_compensation_guide.md` (Tool wear progression, convective chip evacuation, and thermal dissipation thresholds).  
- **Tier 3 (Demonstration Knowledge):** `demo_operating_procedures.md` (Standard CNC operating envelope for demo scenarios, explicitly labeled).

---

## Architecture Decisions

### DECISION-004
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Architecture  
**Decision:** SQLite (MVP) over PostgreSQL  
**Justification:** Zero-configuration in-process database that eliminates external network dependencies during development and local demonstration. Cleanly abstracted via SQLAlchemy ORM; upgrading to PostgreSQL requires only modifying `DATABASE_URL` in `.env`.

---

### DECISION-005
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Architecture  
**Decision:** ChromaDB (Embedded) with Local ONNX MiniLM Embeddings  
**Justification:** Runs locally with persistent disk storage (`rag/vectorstore/chroma_db`), avoiding cloud vector database quotas and network latency.

---

### DECISION-006
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Agent  
**Decision:** Root-Cause Analysis (RCA) implemented as a capability of Quality Analysis Agent  
**Justification:** Problem Statement #37 specifies exactly 4 agents. RCA combines statistical deviations from Process Monitoring, global feature importance from Defect Prediction, and supporting documents retrieved via RAG.

---

## ML Decisions

### DECISION-007
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** ML  
**Decision:** XGBoost Classifier selected for Defect Prediction  
**Alternatives considered (Experiment 1 — Multi-Model Comparison on Validation Set):**  

| Model | Train F1 | Train PR-AUC | Val F1 | Val PR-AUC | Val ROC-AUC |
|-------|----------|--------------|--------|------------|-------------|
| Logistic Regression | 0.5005 | 0.5583 | 0.4767 | 0.5454 | 0.7291 |
| Random Forest | 0.9969 | 1.0000 | 0.7200 | 0.7946 | 0.9276 |
| **XGBoost (Selected)** | **1.0000** | **1.0000** | **0.6977** | **0.8300** | **0.9405** |

**Final Test Set Evaluation (Unseen Data):**  
- Test F1: **0.8217**  
- Test PR-AUC: **0.9198**  
- Test ROC-AUC: **0.9755**  
**Justification:** XGBoost achieved the highest validation Precision-Recall AUC (0.8300) and generalized exceptionally well to the final test set (PR-AUC 0.9198).

---

### DECISION-008
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** ML  
**Decision:** Dual Anomaly Detection (Isolation Forest + IQR Statistical Thresholds on Raw Data)  
**Alternatives considered:** Mahalanobis distance, pure statistical limits, pure autoencoder  
**Justification:** Fitting on raw physical unscaled training records ensures statistical bounds represent genuine physical units (e.g. Kelvin, RPM, Nm). Isolation Forest catches multivariate non-linear correlations, while IQR provides immediate parameter-level explanations.

---

### DECISION-009
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** ML  
**Decision:** SHAP (TreeExplainer) with Native Feature Importance Fallback  
**Alternatives considered:** Permutation importance, LIME  
**Justification:** TreeExplainer computes exact Shapley values in polynomial time for tree ensembles, providing mathematically sound attribution for both global rankings and local single-prediction breakdowns.

---

### DECISION-010
**Date:** 2026-09-23  
**Status:** ACCEPTED  
**Category:** Agent  
**Decision:** Tri-Partite Evidential Basis for Optimization Recommendations  
**Justification:** Prohibits LLM hallucination of numerical adjustments. All suggestions originate from:
1. Rule-based comparison against empirical 5th-95th percentile operating ranges.
2. Historical normal-class baseline queries.
3. What-if model inference calculating predicted defect probability drops under parameter shifts.
