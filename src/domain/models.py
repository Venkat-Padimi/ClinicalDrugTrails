"""Strongly typed domain models for Clinical Trial Site Selection & Recruitment Agent.

All models are defined with Pydantic for validation, serialization, and type safety.
Explicitly labels all data as synthetic.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, date


# ==========================================
# Enums
# ==========================================

class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNCERTAIN = "UNCERTAIN"


class CriterionType(str, Enum):
    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"


class CriterionCategory(str, Enum):
    AGE = "AGE"
    DISEASE_STAGE = "DISEASE_STAGE"
    BIOMARKER = "BIOMARKER"
    PRIOR_TREATMENT = "PRIOR_TREATMENT"
    LAB_VALUE = "LAB_VALUE"
    COMORBIDITY = "COMORBIDITY"
    MEDICATION = "MEDICATION"
    CONSENT = "CONSENT"
    GEOGRAPHY = "GEOGRAPHY"


class DeviationSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeviationCategory(str, Enum):
    INFORMED_CONSENT = "INFORMED_CONSENT"
    INVESTIGATIONAL_PRODUCT = "INVESTIGATIONAL_PRODUCT"
    VISIT_WINDOW = "VISIT_WINDOW"
    LAB_PROTOCOL = "LAB_PROTOCOL"
    INCLUSION_VIOLATION = "INCLUSION_VIOLATION"
    SAFETY_REPORTING = "SAFETY_REPORTING"
    DOCUMENTATION = "DOCUMENTATION"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HumanDecisionType(str, Enum):
    APPROVE = "APPROVE"
    MODIFY = "MODIFY"
    REJECT = "REJECT"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"


class ReviewItemType(str, Enum):
    PATIENT_ELIGIBILITY = "PATIENT_ELIGIBILITY"
    SITE_RISK = "SITE_RISK"
    SITE_RANKING = "SITE_RANKING"
    PROTOCOL_DEVIATION = "PROTOCOL_DEVIATION"


# ==========================================
# Domain Entities
# ==========================================

class EligibilityCriterion(BaseModel):
    """Structured criterion used to evaluate patient eligibility."""
    criterion_id: str
    criterion_type: CriterionType
    category: CriterionCategory
    field_name: str
    operator: str  # '>=', '<=', '==', 'in', 'not_in', 'exists', 'is_true', 'between'
    target_value: Any
    description: str
    is_mandatory: bool = True
    is_synthetic: bool = True


class Trial(BaseModel):
    """Clinical Trial definition."""
    trial_id: str
    trial_name: str
    therapeutic_area: str
    phase: str
    target_population: str
    target_enrollment: int
    enrollment_deadline: str
    protocol_version: str = "v1.0"
    inclusion_criteria: List[EligibilityCriterion] = Field(default_factory=list)
    exclusion_criteria: List[EligibilityCriterion] = Field(default_factory=list)
    is_synthetic: bool = True
    disclaimer: str = "Synthetic demonstration trial data — not a real clinical trial protocol."


class Patient(BaseModel):
    """Synthetic patient profile."""
    synthetic_patient_id: str
    age: int
    sex: str
    region: str
    relevant_conditions: List[str] = Field(default_factory=list)
    disease_stage: str
    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    medications: List[str] = Field(default_factory=list)
    lab_values: Dict[str, float] = Field(default_factory=dict)
    prior_treatment: List[str] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list)
    consent_status: bool = True
    screening_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    assigned_site_id: Optional[str] = None
    is_synthetic: bool = True


class PatientScreeningResult(BaseModel):
    """Detailed result of screening a patient against trial criteria."""
    patient_id: str
    status: EligibilityStatus
    confidence: float = Field(ge=0.0, le=1.0)
    matched_inclusion: List[str] = Field(default_factory=list)
    failed_inclusion: List[str] = Field(default_factory=list)
    triggered_exclusion: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    explanation: str
    requires_human_review: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_synthetic: bool = True


class TrialSite(BaseModel):
    """Candidate clinical trial site profile."""
    site_id: str
    site_name: str
    city: str
    state: str
    country: str
    therapeutic_area_experience_years: float
    investigator_experience_years: float
    historical_trials_completed: int
    historical_enrollment: int
    average_monthly_enrollment: float
    screen_failure_rate: float
    dropout_rate: float
    protocol_deviation_rate: float  # historical deviations per 10 patients
    data_query_rate: float          # queries per Case Report Form (CRF)
    activation_time_days: int
    recruitment_start_delay_days: int
    staff_capacity: int             # available study coordinators/staff
    patient_pool_estimate: int
    is_synthetic: bool = True


class EnrollmentRecord(BaseModel):
    """Historical or monitored enrollment event at a site."""
    record_id: str
    site_id: str
    trial_id: str
    month_index: int
    patients_screened: int
    patients_enrolled: int
    screen_failures: int
    dropouts: int
    is_synthetic: bool = True


class ProtocolDeviation(BaseModel):
    """Detailed record of a clinical protocol deviation."""
    deviation_id: str
    site_id: str
    trial_id: str
    category: DeviationCategory
    severity: DeviationSeverity
    occurrence_date: str
    resolved: bool = False
    recurrence: bool = False
    description: str
    site_impact: Optional[str] = None
    is_synthetic: bool = True


class SitePerformance(BaseModel):
    """Deterministic operational and recruitment evaluation of a site."""
    site_id: str
    site_name: str
    enrollment_velocity_score: float = Field(ge=0.0, le=100.0)
    experience_score: float = Field(ge=0.0, le=100.0)
    compliance_score: float = Field(ge=0.0, le=100.0)
    data_quality_score: float = Field(ge=0.0, le=100.0)
    operational_efficiency_score: float = Field(ge=0.0, le=100.0)
    capacity_score: float = Field(ge=0.0, le=100.0)
    composite_performance_score: float = Field(ge=0.0, le=100.0)
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = True


class RecruitmentForecast(BaseModel):
    """Deterministic recruitment projection with uncertainty bounds."""
    trial_id: str
    site_id: Optional[str] = None
    target_enrollment: int
    eligible_patient_pool: int
    expected_monthly_enrollment: float
    time_to_target_months: float
    p10_time_months: float   # Optimistic (fastest 10th percentile)
    p50_time_months: float   # Median / expected
    p90_time_months: float   # Conservative (slowest 90th percentile)
    enrollment_probability: float  # Probability of meeting target by deadline
    recruitment_shortfall: int
    recruitment_risk_level: RiskLevel
    expected_screen_failures: int
    expected_dropout_impact: int
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = True


class SiteRisk(BaseModel):
    """Multi-dimensional risk assessment for a candidate site."""
    site_id: str
    site_name: str
    overall_risk_score: float = Field(ge=0.0, le=100.0)  # Lower is safer, higher is riskier
    risk_level: RiskLevel
    recruitment_risk: float = Field(ge=0.0, le=100.0)
    operational_risk: float = Field(ge=0.0, le=100.0)
    compliance_risk: float = Field(ge=0.0, le=100.0)
    data_quality_risk: float = Field(ge=0.0, le=100.0)
    capacity_risk: float = Field(ge=0.0, le=100.0)
    activation_risk: float = Field(ge=0.0, le=100.0)
    risk_factors: List[str] = Field(default_factory=list)
    mathematical_breakdown: Dict[str, Any] = Field(default_factory=dict)
    requires_human_review: bool = False
    is_synthetic: bool = True


class SiteRanking(BaseModel):
    """Ranked prioritization result for site selection."""
    rank: int
    site_id: str
    site_name: str
    priority_score: float = Field(ge=0.0, le=100.0)  # Higher is better
    confidence: float = Field(ge=0.0, le=1.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    recruitment_estimate_monthly: float
    rationale: str
    requires_review: bool = False
    is_synthetic: bool = True


class HumanReviewDecision(BaseModel):
    """Human-in-the-loop review record."""
    review_id: str
    item_type: ReviewItemType
    item_id: str
    reviewer_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    decision: HumanDecisionType
    justification_notes: str
    override_values: Dict[str, Any] = Field(default_factory=dict)
    applied: bool = True
    is_synthetic: bool = True


class AuditEvent(BaseModel):
    """Immutable audit record for multi-agent execution tracing."""
    event_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    agent_or_node: str
    action: str
    input_summary: str
    output_summary: str
    decision: str
    confidence: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    data_provenance: str = "Synthetic Test Environment"
    execution_latency_ms: float = 0.0
    errors: Optional[str] = None
    is_synthetic: bool = True


class PatientScreeningSummary(BaseModel):
    """Aggregate screening metrics."""
    total_screened: int
    eligible_count: int
    ineligible_count: int
    uncertain_count: int
    eligibility_rate: float
    uncertain_rate: float
    missing_data_count: int
    missing_data_rate: float
    top_exclusion_reasons: Dict[str, int] = Field(default_factory=dict)
    top_failed_inclusion_reasons: Dict[str, int] = Field(default_factory=dict)
    is_synthetic: bool = True


class ProtocolDeviationSummary(BaseModel):
    """Aggregate protocol deviation metrics."""
    total_deviations: int
    severity_breakdown: Dict[DeviationSeverity, int] = Field(default_factory=dict)
    category_breakdown: Dict[DeviationCategory, int] = Field(default_factory=dict)
    unresolved_count: int
    recurrence_count: int
    site_deviation_counts: Dict[str, int] = Field(default_factory=dict)
    facts: List[str] = Field(default_factory=list)
    interpretations: List[str] = Field(default_factory=list)
    is_synthetic: bool = True


class TrialAnalysisResult(BaseModel):
    """Comprehensive analysis outcome containing complete workflow results."""
    trial: Trial
    screening_summary: PatientScreeningSummary
    patient_screening_results: List[PatientScreeningResult] = Field(default_factory=list)
    site_performances: List[SitePerformance] = Field(default_factory=list)
    site_risks: List[SiteRisk] = Field(default_factory=list)
    site_rankings: List[SiteRanking] = Field(default_factory=list)
    recruitment_forecast: RecruitmentForecast
    deviation_summary: ProtocolDeviationSummary
    deviations: List[ProtocolDeviation] = Field(default_factory=list)
    human_reviews: List[HumanReviewDecision] = Field(default_factory=list)
    audit_events: List[AuditEvent] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    synthetic_disclaimer: str = (
        "Synthetic demonstration data — not real clinical trial data. "
        "This output is for decision-support demonstration purposes only."
    )
    is_synthetic: bool = True
