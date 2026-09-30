# System Limitations & Safety Boundary

## Scope of Decision-Support Demonstration

This software is developed strictly as a **decision-support simulation and engineering demonstration**. It is not cleared, certified, or intended for direct clinical or regulatory use without formal clinical trials, Good Clinical Practice (GCP) auditing, and institutional ethics review.

---

## Technical & Clinical Boundaries

1. **Synthetic Patient Data**:
   - The patient population is generated using parametric synthetic models. While ranges and biomarkers mirror real-world oncology and cardiology distributions, they do not account for latent biological interactions or unrecorded comorbidities.

2. **No Autonomous Clinical Decision-Making**:
   - The system is architected so that all borderline or uncertain clinical eligibility outcomes trigger mandatory Human-In-The-Loop review.
   - The system does not claim to diagnose patients or establish medical suitability.

3. **Deterministic Scoring Bounds**:
   - Multi-criteria site scoring relies on historical and monitored metrics (enrollment velocity, query rates, deviation logs). Unprecedented global disruptions (e.g. supply chain failures or unforeseen regulatory holds) cannot be inferred from historical data alone.

4. **Investigator Discretion**:
   - Institutional Review Boards (IRB) and Principal Investigators (PIs) hold sole legal and ethical authority over clinical study site activation and subject enrollment.
