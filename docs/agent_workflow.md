# Multi-Agent Workflow Specification

## Agent Roles & Graph Nodes

The multi-agent architecture is orchestrated through an explicit **LangGraph StateGraph** connecting 11 specialized agent nodes:

```mermaid
sequenceDiagram
    participant TI as Trial Intake Agent
    participant CP as Criteria Parser Agent
    participant PS as Patient Screening Agent
    participant EE as Eligibility Evidence Agent
    participant SI as Site Intelligence Agent
    participant RF as Recruitment Forecast Agent
    participant PD as Protocol Deviation Agent
    participant RA as Risk Assessment Agent
    participant SR as Site Ranking Agent
    participant HR as Human Review Console
    participant RP as Reporting Agent

    TI->>CP: Structured Protocol Definition
    CP->>PS: Parsed Inclusion/Exclusion Rules
    PS->>EE: Patient Cohort Evaluation
    EE->>SI: Validated Evidence & Missing Data Flags
    SI->>RF: Site Performance Metrics
    RF->>PD: Recruitment Horizon & Feasibility
    PD->>RA: Deviation History & GCP Compliance
    RA->>SR: Multi-Dimensional Site Risks
    SR-->>HR: Conditional Route (if Uncertain or High Risk)
    HR->>RP: Human Approved / Overridden Decisions
    SR-->>RP: Direct Route (if Clean & Low Risk)
    RP->>RP: Final TrialAnalysisResult Dossier
```

---

## Node Descriptions

### 1. `trial_intake_node`
- Ingests protocol parameters: target enrollment, development phase, deadline, version, and therapeutic area.
- Emits intake audit event.

### 2. `criteria_parser_node`
- Validates machine-readable rule definitions across age, staging, biomarkers, lab thresholds, and prohibited medications.

### 3. `patient_screening_node`
- Evaluates synthetic cohort records against parsed criteria.
- Classifies each subject as `ELIGIBLE`, `INELIGIBLE`, or `UNCERTAIN`.

### 4. `eligibility_validation_node`
- Inspects evidence completeness and identifies missing lab values.
- Prepares escalation queue for human review.

### 5. `site_intelligence_node`
- Computes operational scores (velocity, experience, compliance, data quality, capacity).

### 6. `recruitment_forecast_node`
- Projects P10, P50, and P90 enrollment curves, calculates screen failure overhead and dropout attrition.

### 7. `protocol_deviation_node`
- Categorizes deviations (LOW, MEDIUM, HIGH, CRITICAL).
- Distinguishes empirical facts from analytical interpretations.
- Detects statistical site outliers ($> \mu + 1.5\sigma$).

### 8. `risk_assessment_node`
- Calculates multi-dimensional risk scores and mathematical breakdowns for each site.

### 9. `site_ranking_node`
- Applies MCDA ranking to produce prioritized candidate site lists.
- Determines whether conditional human escalation is required.

### 10. `human_review_node`
- Manages human-in-the-loop review queue for uncertain patients or high-risk sites.
- Records explicit reviewer ID, rationale, and override values.

### 11. `reporting_node`
- Compiles the final immutable `TrialAnalysisResult` object for UI rendering and export.
