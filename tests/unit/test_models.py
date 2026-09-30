"""Unit tests for domain models."""

import pytest
from src.domain.models import (
    EligibilityCriterion,
    CriterionType,
    CriterionCategory,
    EligibilityStatus,
    Trial,
    Patient,
    PatientScreeningResult,
    TrialSite,
    ProtocolDeviation,
    DeviationSeverity,
    DeviationCategory,
    SitePerformance,
    RecruitmentForecast,
    RiskLevel,
    SiteRisk,
    SiteRanking,
    HumanReviewDecision,
    HumanDecisionType,
    ReviewItemType,
    AuditEvent,
)

def test_eligibility_criterion_instantiation():
    crit = EligibilityCriterion(
        criterion_id="INC-01",
        criterion_type=CriterionType.INCLUSION,
        category=CriterionCategory.AGE,
        field_name="age",
        operator=">=",
        target_value=18,
        description="Adult patients aged 18 or older"
    )
    assert crit.criterion_id == "INC-01"
    assert crit.operator == ">="
    assert crit.is_synthetic is True

def test_trial_model():
    trial = Trial(
        trial_id="NCT099901",
        trial_name="Phase III NSCLC Synthetic Evaluation",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Non-Small Cell Lung Cancer Stage IIIB/IV",
        target_enrollment=150,
        enrollment_deadline="2027-12-31"
    )
    assert trial.target_enrollment == 150
    assert "Synthetic" in trial.disclaimer
    assert trial.is_synthetic is True

def test_patient_model_and_screening():
    patient = Patient(
        synthetic_patient_id="SYN-PT-001",
        age=58,
        sex="Female",
        region="Midwest",
        relevant_conditions=["NSCLC"],
        disease_stage="Stage IV",
        biomarkers={"EGFR": "L858R", "PD-L1": 65.0},
        lab_values={"eGFR": 78.5, "platelets": 210000.0, "ALT": 24.0},
        prior_treatment=["Platinum-doublet"],
        comorbidities=["Hypertension"]
    )
    assert patient.age == 58
    assert patient.is_synthetic is True

    result = PatientScreeningResult(
        patient_id=patient.synthetic_patient_id,
        status=EligibilityStatus.ELIGIBLE,
        confidence=0.95,
        matched_inclusion=["INC-01", "INC-02"],
        failed_inclusion=[],
        triggered_exclusion=[],
        explanation="Patient satisfies all age and biomarker criteria."
    )
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.confidence == 0.95

def test_site_and_deviation_models():
    site = TrialSite(
        site_id="SITE-101",
        site_name="Metro Academic Cancer Center",
        city="Chicago",
        state="IL",
        country="USA",
        therapeutic_area_experience_years=12.5,
        investigator_experience_years=15.0,
        historical_trials_completed=28,
        historical_enrollment=340,
        average_monthly_enrollment=4.5,
        screen_failure_rate=0.18,
        dropout_rate=0.08,
        protocol_deviation_rate=0.4,
        data_query_rate=1.2,
        activation_time_days=65,
        recruitment_start_delay_days=10,
        staff_capacity=8,
        patient_pool_estimate=450
    )
    assert site.historical_enrollment == 340
    assert site.is_synthetic is True

    dev = ProtocolDeviation(
        deviation_id="DEV-001",
        site_id="SITE-101",
        trial_id="NCT099901",
        category=DeviationCategory.VISIT_WINDOW,
        severity=DeviationSeverity.LOW,
        occurrence_date="2026-03-15",
        resolved=True,
        recurrence=False,
        description="Patient visit conducted 1 day outside protocol window."
    )
    assert dev.severity == DeviationSeverity.LOW
    assert dev.is_synthetic is True

def test_human_review_and_audit():
    decision = HumanReviewDecision(
        review_id="REV-100",
        item_type=ReviewItemType.PATIENT_ELIGIBILITY,
        item_id="SYN-PT-001",
        reviewer_id="MD-REVIEWER-7",
        decision=HumanDecisionType.APPROVE,
        justification_notes="Borderline lab value verified clinically acceptable under synthetic protocol rule."
    )
    assert decision.decision == HumanDecisionType.APPROVE

    audit = AuditEvent(
        event_id="EVT-001",
        agent_or_node="EligibilityEvidenceAgent",
        action="EVALUATE_PATIENT",
        input_summary="Patient SYN-PT-001",
        output_summary="ELIGIBLE",
        decision="ELIGIBLE",
        confidence=0.98
    )
    assert audit.agent_or_node == "EligibilityEvidenceAgent"
