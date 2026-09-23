# IndustrialGuard AI — Final Demo Contract

This document defines the **fixed, non-negotiable end-to-end demonstration workflow**.

The entire project is built around making this one workflow polished, reliable, and reproducible.
Every 🔴 MUST HAVE item exists to support this demo path.

---

## Demo Scenario: "Batch 2024-001 Incident"

This scenario walks through one manufacturing batch progressing from normal operation to a predicted defect, through explanation, recommendation, and human decision.

---

## Required Demo Steps (in order)

### Step 1 — Normal Operation (T=0)
**Show in dashboard:**
- All process parameters within normal operating ranges
- Process health: GREEN
- Defect risk: LOW
- Anomaly count: 0

**What this demonstrates:** The system correctly identifies normal operation and does not generate false alarms.

---

### Step 2 — Parameter Deviation Detected (T=1)
**Trigger:** Introduce a process record where one or more parameters deviate from normal (real dataset sample or labeled synthetic stream).

**Show in dashboard:**
- One or more parameters flagged by Process Monitoring Agent
- Parameter deviation highlighted on monitoring chart
- Alert banner: "Process deviation detected — forwarding to Quality Analysis"

**What this demonstrates:** The Process Monitoring Agent detects changes in real time (simulated stream) and routes structured output downstream.

---

### Step 3 — Anomaly Detected (T=2)
**Show in dashboard:**
- Anomaly Detection panel: "ANOMALY DETECTED"
- Severity level shown
- Affected parameters listed
- Timestamp recorded

**System output (must be structured, not free-text):**
```json
{
  "status": "ABNORMAL",
  "anomalies": [
    {"parameter": "<param>", "current_value": <val>, "normal_range": [<low>, <high>], "severity": "HIGH"}
  ],
  "forwarded_to": "quality_analysis_agent"
}
```

**What this demonstrates:** Anomaly detection runs on ML/statistical evidence, not an LLM.

---

### Step 4 — Defect Risk Predicted (T=3)
**Show in dashboard:**
- Defect Prediction panel: "DEFECT RISK: HIGH"
- Predicted defect probability: XX% (real model output)
- Confidence/probability bar
- Historical comparison: "Last 10 similar process states — X% resulted in defects"

**System output:**
```json
{
  "prediction": "DEFECTIVE",
  "probability": <real_model_output>,
  "model_version": "v1.0",
  "contributing_features": [
    {"feature": "<feature_1>", "importance": <val>},
    {"feature": "<feature_2>", "importance": <val>}
  ]
}
```

**What this demonstrates:** Defect prediction is a trained ML model, not LLM inference.

---

### Step 5 — Explainability (T=4)
**Show in dashboard:**
- Why was this batch flagged?
- Feature importance / SHAP bar chart
- Clear labels distinguishing: model evidence vs statistical relationship vs retrieved documentation vs LLM interpretation

**What this demonstrates:** XAI layer — engineers can see *why* the prediction was made, not just *what* it predicted.

**Critical point to demonstrate:** Causal language is avoided. The dashboard says "associated with elevated defect risk" not "caused by".

---

### Step 6 — RAG Evidence Retrieved (T=5)
**Show in dashboard / chat:**
- Retrieved passage from knowledge base (with source citation)
- Passage is relevant to the top contributing feature from Step 4
- Source labeled: TIER 1 / TIER 2 / TIER 3

**Example (illustrative, fill with real source):**
> "Elevated vibration in spindle bearings is associated with accelerated wear and dimensional inaccuracies in machined parts. Recommended inspection interval: [source]."

**What this demonstrates:** RAG is load-bearing — it augments the ML finding, it doesn't replace it.

---

### Step 7 — Recommendation Generated (T=6)
**Show in dashboard:**
- Recommended action
- Evidence basis: which of the three valid derivation methods was used
  - (a) Parameter outside validated operating range → adjust toward range
  - (b) Historical: low-defect records had different value
  - (c) What-if: model predicts probability drops from X% to Y% if parameter is adjusted
- Uncertainty explicitly stated where evidence is insufficient
- Source reference if RAG-backed

**System output:**
```json
{
  "recommendation": "<action>",
  "basis": "what_if_inference",
  "evidence": {
    "current_predicted_probability": <val>,
    "adjusted_predicted_probability": <val>,
    "parameter_change": {"feature": "<f>", "from": <a>, "to": <b>}
  },
  "rag_source": "<source title + tier>",
  "uncertainty": "moderate"
}
```

**What this demonstrates:** Recommendations are never invented by the LLM. They are traceable to ML evidence.

---

### Step 8 — Human Engineer Reviews (T=7)
**Show in dashboard:**
- Human-in-the-loop panel
- Engineer can: APPROVE recommendation / REJECT recommendation / REQUEST MORE INFO
- Engineer can record corrective action taken
- Audit trail saved to database

**What this demonstrates:** Responsible AI — the system is a decision-support tool. No autonomous machine control.

---

### Step 9 — Automated Quality Report Generated (T=8)
**Show in dashboard or chat:**
- Narrative report generated by Granite (IBM LLM)
- Grounded in: anomaly data + model output + RAG evidence
- Clearly labeled: "AI-generated report — requires engineer review"
- Granite may NOT invent numbers not present in the structured inputs

**What this demonstrates:** Granite's role is narration and synthesis, not numerical analysis.

---

## Demo Prerequisites

Before running the demo, verify:
- [ ] Demo dataset record is loaded in the database
- [ ] ML model is loaded (`ml/models/` — version documented)
- [ ] Anomaly detector is fitted
- [ ] ChromaDB vector store is populated
- [ ] LangFlow workflow is running
- [ ] FastAPI backend is running
- [ ] Next.js frontend is running
- [ ] IBM watsonx.ai / Granite API key is valid

---

## Demo Failure Recovery Plan

| Failure | Recovery |
|---------|----------|
| IBM API unavailable | Switch to pre-cached Granite response (saved from earlier run). Label: "CACHED DEMO RESPONSE" |
| LangFlow not responding | Call ML modules directly from FastAPI. Document the skip. |
| Vector store unavailable | Use pre-retrieved RAG passage stored in `data/synthetic/demo_rag_passages.json` |
| Model prediction unavailable | Show last saved prediction from DB. Label: "CACHED PREDICTION" |

The demo must complete end-to-end even in degraded mode. Partial failures must be labeled, not hidden.

---

## What the Demo Explicitly Does NOT Show

- Live factory sensor connection
- Autonomous machine control
- Guaranteed defect prevention
- Causal certainty ("X caused the defect")
- Real-time IoT integration

These limitations are stated in the dashboard footer and README.
