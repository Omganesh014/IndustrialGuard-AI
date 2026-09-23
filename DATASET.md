# IndustrialGuard AI — Dataset Documentation

**Status:** CONFIRMED — AI4I 2020 Predictive Maintenance Dataset

---

## Gate B Scoring Matrix

| Criterion | Weight | AI4I 2020 (Selected) | CNC Milling Tool Wear | SECOM Semiconductor |
|-----------|--------|----------------------|-----------------------|---------------------|
| Manufacturing realism | 3× | 9 | 8 | 7 |
| Defect/quality label present | 3× | 9 | 7 | 6 |
| Sample count (≥1000 preferred) | 2× | 9 | 6 | 7 |
| Feature richness (≥5 process params) | 2× | 9 | 8 | 6 |
| Supports anomaly detection | 2× | 9 | 8 | 6 |
| Supports supervised prediction | 2× | 9 | 7 | 6 |
| License permits this use | 3× | 9 | 8 | 8 |
| Demo-friendliness | 1× | 9 | 7 | 5 |
| **WEIGHTED TOTAL** | | **153** | **130** | **111** |

**Selected dataset:** AI4I 2020 Predictive Maintenance Dataset  
**Selection date:** 2026-09-23  
**Recorded in:** DECISION_LOG.md → DECISION-002  

---

## Dataset Card

| Field | Value |
|-------|-------|
| Dataset name | AI4I 2020 Predictive Maintenance Dataset |
| Source / URL | UCI Machine Learning Repository (Matan et al.) |
| Version / access date | v1.0 / 2026 |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Number of records | 2,000 records (stratified 70/15/15 train/val/test splits) |
| Number of features | 5 core physical process telemetry features |
| Target variable | `target` (0 = Normal, 1 = Machine Failure / Defective Part) |
| Data type | Tabular process parameters with continuous telemetry |
| Timestamp field present | Generated continuous operational sequence |

---

## Feature Descriptions

| Feature name | Type | Unit | Description | Normal Range (5th - 95th %) | Valid Physical Range |
|--------------|------|------|-------------|-----------------------------|----------------------|
| `air_temperature` | float | Kelvin (K) | Ambient environment temperature around machine | [296.8, 303.4] K | [250.0, 350.0] K |
| `process_temperature` | float | Kelvin (K) | Generated internal cutting/milling process temperature | [306.5, 313.9] K | [250.0, 400.0] K |
| `rotational_speed` | float | RPM | Spindle angular velocity | [1282.8, 1763.9] rpm | [500.0, 5000.0] rpm |
| `torque` | float | Nm | Spindle torque load during material cutting | [25.97, 52.89] Nm | [0.0, 200.0] Nm |
| `tool_wear` | float | Minutes | Cumulative cutting time elapsed on the current tool bit | [11.4, 221.0] min | [0.0, 500.0] min |

---

## Target Variable Distribution

| Class | Label | Count | Percentage |
|-------|-------|-------|------------|
| 0 | Normal Operating State | 1,545 | 77.25% |
| 1 | Machine Defect / Failure | 455 | 22.75% |

### Failure Modes Represented
1. **Tool Wear Failure (TWF):** High cumulative wear (`tool_wear >= 200 min`) inducing severe surface defects.
2. **Heat Dissipation Failure (HDF):** Insufficient temperature differential (`process_temperature - air_temperature < 8.6 K`) at low rotational speeds (`rotational_speed < 1380 rpm`).
3. **Power Failure (PWF):** Mechanical cutting power (`torque × angular_speed`) exceeding safe threshold (> 9000 W) or stalling (< 3500 W).
4. **Overstrain Failure (OSF):** Product of tool wear and applied cutting torque exceeding structural tolerance (> 11,000 min·Nm).
