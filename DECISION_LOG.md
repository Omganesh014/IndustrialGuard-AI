# IndustrialGuard AI — Decision Log

This log records every major architecture, dataset, model, and design decision.
It is the authoritative source for justifying choices during code review, viva, or technical interviews.

**Rule:** Every decision here must be traceable to evidence — benchmark results, gate checks, or documented constraints.
No decision should read "because it is popular" without a supporting technical reason.

---

## Decision Record Format

```
DECISION-NNN
Date:
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
**Date:** [Fill after Gate A check]
**Status:** PROPOSED
**Category:** Architecture
**Decision:** IBM watsonx.ai + Granite + LangFlow (Option A)
**Alternatives considered:**
- Option B: IBM Cloud Agentic Lab + Granite
- Option C: LangChain + RAG + Granite (fallback)
**Justification:** [Fill after verifying IBM Cloud access, Granite availability, LangFlow connectivity, and quota sufficiency]
**Note:** If IBM access is unavailable by Day 0 end, immediately supersede with Option C (LangChain + RAG + Granite) and record that decision here. Do not debug access past Day 0.

---

### DECISION-002
**Date:** [Fill after Gate B check]
**Status:** PROPOSED
**Category:** Dataset
**Decision:** [Dataset name — fill after Gate B scoring]
**Alternatives considered:**

| Criterion | Dataset A | Dataset B | Dataset C |
|-----------|-----------|-----------|-----------|
| Manufacturing realism | | | |
| Defect/quality label present | | | |
| Sample count | | | |
| Feature richness | | | |
| Supports anomaly detection | | | |
| Supports supervised prediction | | | |
| License permits this use | | | |
| Demo-friendliness | | | |
| **TOTAL** | | | |

**Justification:** [Fill from scoring matrix]
**If no defect label found:** Reframe to anomaly-only detection. Document here: "Supervised defect classification is not possible with this dataset because [reason]. The system uses anomaly detection and severity scoring instead."

---

### DECISION-003
**Date:** [Fill after Gate C check]
**Status:** PROPOSED
**Category:** RAG
**Decision:** [RAG source list]
**Alternatives considered:** [Other sources checked]
**Justification:** [Confirmed public availability, license, relevance to chosen manufacturing scenario]
**Tier classification:**
- Tier 1 (public standards, government/university docs): [list]
- Tier 2 (manufacturer public docs, open-source manuals): [list]
- Tier 3 (project-generated synthetic docs, labeled "Project-generated demonstration knowledge"): [list]

---

## Architecture Decisions

### DECISION-004
**Date:** [Fill]
**Status:** PROPOSED
**Category:** Architecture
**Decision:** SQLite (MVP) over PostgreSQL
**Justification:** Fewer moving parts before demo day. SQLite runs in-process, requires zero server setup, and can be migrated to PostgreSQL without changing the ORM layer. Will upgrade only if multi-user concurrency is required.

---

### DECISION-005
**Date:** [Fill]
**Status:** PROPOSED
**Category:** Architecture
**Decision:** ChromaDB (embedded) over hosted vector DB
**Justification:** Matches the SQLite rationale — zero additional services. ChromaDB in embedded mode stores to disk, has the same retrieval interface as hosted options, and can be swapped by changing one config line.

---

### DECISION-006
**Date:** [Fill]
**Status:** PROPOSED
**Category:** Agent
**Decision:** Root-Cause Analysis implemented as a capability shared by Quality Analysis Agent and Defect Prediction Agent, NOT as a 5th independent agent.
**Justification:** Problem Statement #37 specifies exactly 4 agents. Adding a 5th agent adds orchestration complexity without new capability. RCA = feature importance output from the Defect Prediction Agent + contextual interpretation by the Quality Analysis Agent + RAG-retrieved evidence. This satisfies the RCA requirement within the 4-agent constraint.

---

## ML Decisions

### DECISION-007
**Date:** [Fill after model comparison]
**Status:** PROPOSED
**Category:** ML
**Decision:** [Primary defect prediction model — fill after experiments]
**Alternatives considered:** [Results from Experiment 1 — multi-model comparison]
**Justification:** [Based on validation F1/ROC-AUC/PR-AUC — fill from actual evaluation]

---

### DECISION-008
**Date:** [Fill]
**Status:** PROPOSED
**Category:** ML
**Decision:** [Anomaly detection approach — fill after Experiment 2]
**Alternatives considered:** [Isolation Forest vs statistical thresholds vs other]
**Justification:** [Data characteristics — e.g., unlabeled normal/abnormal, dimensionality, distribution]

---

### DECISION-009
**Date:** [Fill]
**Status:** PROPOSED
**Category:** ML
**Decision:** [Explainability method — SHAP or feature importance]
**Alternatives considered:** SHAP, permutation importance, model-native feature importance
**Justification:** [Time constraints + data scale. SHAP preferred if compute time is acceptable on dataset size.]

---

## Process Optimization Decisions

### DECISION-010
**Date:** [Fill]
**Status:** PROPOSED
**Category:** Agent
**Decision:** Recommendations derived from one or more of: (a) rule-based parameter ranges, (b) historical low-defect operating conditions, (c) what-if model inference
**Justification:** LLM must NOT invent numerical parameter adjustments without one of these three evidential bases. This ensures every recommendation can be explained during a technical interview as: "The model predicted defect probability dropped from X% to Y% when we shifted parameter Z from value A to value B in a what-if inference."

---

## Superseded Decisions

*[Record decisions here when they are replaced and why.]*
