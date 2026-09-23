# ISO 13374: Condition Monitoring and Diagnostics of Machine Systems

**Tier: 1 (International Technical Standard)**
**Source: ISO / TC 108 / SC 5**

## 1. Scope & General Principles
ISO 13374 establishes general guidelines and information architecture for software systems processing condition monitoring and machine diagnostic data. The standard delineates six distinct processing layers:
1. Data Acquisition (DA): Collection of raw digital sensory signals (temperature, torque, vibration).
2. Data Manipulation (DM): Feature extraction, signal filtering, statistical descriptor computation (IQR, RMS, kurtosis).
3. State Detection (SD): Comparing extracted features against baseline operating limits to identify abnormal physical states.
4. Health Assessment (HA): Determining defect probability and degradation severity based on historical operating profiles.
5. Prognostics (PR): Estimating remaining useful life (RUL) and anticipating failure progression.
6. Advisory Generation (AG): Producing recommended operational adjustments or maintenance actions for qualified engineering personnel.

## 2. Thresholding and Anomaly Detection
Condition indicators derived from rotating machinery parameters must be evaluated using multi-tier thresholds:
- Alert Limit (Normal Operating Envelope): Defined by the 90th or 95th percentile of fault-free baseline operational data.
- Action Limit: When parameters exceed statistical deviation bounds (typically > 2.5 to 3.0 times the Interquartile Range above baseline), immediate root-cause investigation is recommended.
- Simultaneous multi-parameter shifts (e.g., combined elevated tool wear and sudden torque spike) indicate high-risk non-linear degradation requiring process pause or tool replacement.

## 3. Human Supervision Requirement
Automated diagnostic systems complying with ISO 13374 Advisory Generation standards operate as decision-support mechanisms. All prescriptive control recommendations must be verified and authorized by human engineering specialists before execution.
