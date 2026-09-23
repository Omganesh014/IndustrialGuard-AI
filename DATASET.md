# IndustrialGuard AI — Dataset Documentation

**Status:** [FILL AFTER GATE B — nothing below is confirmed until Gate B closes]

---

## Gate B Scoring Matrix

Complete this table before locking the dataset.
Select the dataset with the highest total score. Document ties and tiebreakers.

| Criterion | Weight | Dataset A | Dataset B | Dataset C |
|-----------|--------|-----------|-----------|-----------|
| Manufacturing realism | 3× | | | |
| Defect/quality label present | 3× | | | |
| Sample count (≥1000 preferred) | 2× | | | |
| Feature richness (≥5 process params) | 2× | | | |
| Supports anomaly detection | 2× | | | |
| Supports supervised prediction | 2× | | | |
| License permits this use | 3× | | | |
| Demo-friendliness | 1× | | | |
| **WEIGHTED TOTAL** | | | | |

**Selected dataset:** [FILL]
**Selection date:** [FILL]
**Recorded in:** DECISION_LOG.md → DECISION-002

---

## Dataset Card (fill after Gate B)

| Field | Value |
|-------|-------|
| Dataset name | [FILL] |
| Source / URL | [FILL] |
| Version / access date | [FILL] |
| License | [FILL] |
| Number of records | [FILL — no fabrication] |
| Number of features | [FILL] |
| Target variable | [FILL or "None — see reframing note"] |
| Data type | Tabular / Time-series / Mixed |
| Timestamp field present | Yes / No |

---

## Feature Descriptions

| Feature name | Type | Unit | Description | Missing values | Notes |
|--------------|------|------|-------------|----------------|-------|
| [feature_1] | | | | | |
| [feature_2] | | | | | |
| ... | | | | | |

---

## Target Variable

If a defect label exists:

| Class | Label | Count | Percentage |
|-------|-------|-------|------------|
| Normal | 0 | [FILL] | [FILL]% |
| Defective | 1 | [FILL] | [FILL]% |

**Class imbalance note:** [FILL — e.g., "Dataset is imbalanced at X:Y ratio. Will use PR-AUC / F1 as primary metrics, not accuracy."]

If NO defect label:
> **Reframing note:** This dataset does not contain a validated defect label. Supervised defect classification is therefore not performed. The system uses anomaly detection and deviation severity scoring instead. This is documented in DECISION_LOG.md → DECISION-002 and stated explicitly in all dashboards and reports.

---

## Data Quality

| Issue | Presence | Handling approach |
|-------|----------|-------------------|
| Missing values | [Yes/No — count] | [strategy] |
| Duplicate rows | [Yes/No — count] | [strategy] |
| Outliers | [Yes/No] | [strategy] |
| Class imbalance | [ratio] | [strategy] |
| Feature leakage risk | [identified fields] | [strategy] |

---

## Train / Validation / Test Split

| Split | Proportion | Purpose |
|-------|-----------|---------|
| Train | [e.g., 70%] | Model training |
| Validation | [e.g., 15%] | Hyperparameter tuning |
| Test | [e.g., 15%] | Final evaluation only — not used during development |

**Leakage prevention:** Scaling parameters fit on training set only. No test-set information used before final evaluation.

---

## Data Provenance Labels

All data in the running application is labeled as one of:

- `REAL PUBLIC DATA` — original dataset, unmodified
- `SYNTHETIC DATA` — project-generated data for demo gaps; never presented as real industrial data
- `SIMULATED STREAM` — historical records replayed in sequence to simulate real-time feed
- `USER-PROVIDED DATA` — uploaded by engineer at runtime

---

## Limitations

[FILL after understanding the dataset]

Examples of valid limitations:
- "Dataset represents a single machine/process type; generalization is not validated."
- "No timestamps present; temporal anomaly detection is not applicable."
- "Defect labels are binary; multi-class defect type prediction is not supported."
- "Dataset size is modest (N=XXXX); deep learning approaches are not justified."
