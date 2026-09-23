# Project-generated demonstration knowledge: Standard Operating Guidelines

**Tier: 3 (Project-Generated Synthetic Demonstration Knowledge)**
**Source: Project-generated demonstration knowledge — internal engineering SOP**

## 1. Notice of Provenance
This document constitutes project-generated demonstration knowledge created specifically for evaluating the IndustrialGuard AI decision-support pipeline. It is not an official industrial certification standard.

## 2. Standard Machine Tool Operating Envelope (Batch 2024 Scenarios)
For standard 5-axis CNC vertical machining centers in the demo cell:
- Air Temperature: Normal baseline 298.0 K to 302.0 K. Ambient ventilation alert if air temperature exceeds 304.5 K.
- Process Temperature: Normal cutting baseline 308.0 K to 312.0 K.
- Rotational Speed: Standard operating envelope is 1400 to 1750 rpm for medium-tensile steel roughing.
- Cutting Torque: Nominal range 35.0 to 55.0 Nm. Continuous torque above 60.0 Nm indicates excessive tool load.
- Tool Wear Threshold: Safe operation up to 180 minutes. High defect risk when tool wear exceeds 200 minutes.

## 3. Protocol for High-Risk Machine Status
When IndustrialGuard AI triggers an ELEVATED or HIGH risk level:
1. The machine operator must pause automatic cycle start.
2. Review the top contributing features flagged by the Quality Analysis Agent.
3. If tool wear is the primary factor, inspect cutting edges under magnification.
4. If torque or thermal anomalies are flagged, verify coolant pressure and spindle lubrication.
5. Record approval or rejection with reviewer ID in the Human-in-the-Loop review log.
