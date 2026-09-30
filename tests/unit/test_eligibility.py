"""Unit tests for the Deterministic Eligibility Criteria Engine."""

import pytest
from src.domain.models import (
    Trial,
    Patient,
    EligibilityCriterion,
    CriterionType,
    CriterionCategory,
    EligibilityStatus,
)
from src.engines.eligibility_engine import EligibilityCriteriaEngine

@pytest.fixture
def sample_trial():
    return Trial(
        trial_id="TEST-TRIAL-01",
        trial_name="Test Trial Oncology",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults with NSCLC",
        target_enrollment=50,
        enrollment_deadline="2027-12-31",
        inclusion_criteria=[
            EligibilityCriterion(
                criterion_id="INC-AGE",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.AGE,
                field_name="age",
                operator="between",
                target_value=[18, 75],
                description="Age 18-75",
            ),
            EligibilityCriterion(
                criterion_id="INC-STAGE",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.DISEASE_STAGE,
                field_name="disease_stage",
                operator="in",
                target_value=["Stage IIIB", "Stage IV"],
                description="Advanced NSCLC",
            ),
            EligibilityCriterion(
                criterion_id="INC-EGFR-LAB",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.LAB_VALUE,
                field_name="eGFR",
                operator=">=",
                target_value=50.0,
                description="eGFR >= 50",
            ),
            EligibilityCriterion(
                criterion_id="INC-CONSENT",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.CONSENT,
                field_name="consent_status",
                operator="is_true",
                target_value=True,
                description="Consent provided",
            ),
        ],
        exclusion_criteria=[
            EligibilityCriterion(
                criterion_id="EXC-COMORB",
                criterion_type=CriterionType.EXCLUSION,
                category=CriterionCategory.COMORBIDITY,
                field_name="comorbidities",
                operator="contains_any",
                target_value=["Brain Metastases"],
                description="No untreated brain metastases",
            ),
            EligibilityCriterion(
                criterion_id="EXC-MED",
                criterion_type=CriterionType.EXCLUSION,
                category=CriterionCategory.MEDICATION,
                field_name="medications",
                operator="contains_any",
                target_value=["Prohibited Drug X"],
                description="No Prohibited Drug X",
            ),
        ],
    )

def test_eligible_patient(sample_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="PT-OK",
        age=55,
        sex="Female",
        region="Midwest",
        disease_stage="Stage IV",
        lab_values={"eGFR": 65.0, "platelets": 180000.0},
        medications=["Metformin"],
        comorbidities=["Hypertension"],
        consent_status=True,
    )
    result = engine.evaluate_patient(patient, sample_trial)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.confidence >= 0.95
    assert result.requires_human_review is False
    assert len(result.matched_inclusion) == 4
    assert len(result.failed_inclusion) == 0
    assert len(result.triggered_exclusion) == 0

def test_failed_inclusion_patient(sample_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="PT-FAIL-AGE",
        age=82,  # > 75
        sex="Male",
        region="Northeast",
        disease_stage="Stage IV",
        lab_values={"eGFR": 55.0},
        medications=[],
        comorbidities=[],
        consent_status=True,
    )
    result = engine.evaluate_patient(patient, sample_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.failed_inclusion) == 1
    assert "INC-AGE" in result.failed_inclusion[0]

def test_triggered_exclusion_patient(sample_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="PT-EXC-COMORB",
        age=50,
        sex="Female",
        region="West",
        disease_stage="Stage IV",
        lab_values={"eGFR": 60.0},
        medications=[],
        comorbidities=["Brain Metastases", "Hypertension"],
        consent_status=True,
    )
    result = engine.evaluate_patient(patient, sample_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.triggered_exclusion) == 1
    assert "EXC-COMORB" in result.triggered_exclusion[0]

def test_missing_data_triggers_uncertain_review(sample_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="PT-MISSING-LAB",
        age=50,
        sex="Male",
        region="South",
        disease_stage="Stage IV",
        lab_values={},  # Missing eGFR!
        medications=[],
        comorbidities=[],
        consent_status=True,
    )
    result = engine.evaluate_patient(patient, sample_trial)
    assert result.status == EligibilityStatus.UNCERTAIN
    assert result.requires_human_review is True
    assert len(result.missing_information) >= 1
    assert "eGFR" in result.missing_information[0]
