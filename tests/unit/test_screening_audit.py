"""Detailed Patient Screening Audit Tests.

Verifies deterministic rule evaluation and explanation accuracy across:
1. Clearly eligible patient
2. Clearly ineligible patient
3. Patient failing an inclusion criterion (e.g. age or lab threshold)
4. Patient triggering an exclusion criterion (e.g. prohibited medication or comorbidity)
5. Patient with missing laboratory data
6. Ambiguous patient requiring human review
"""

import pytest
from src.domain.models import (
    Trial,
    Patient,
    EligibilityStatus,
    EligibilityCriterion,
    CriterionType,
    CriterionCategory,
)
from src.engines.eligibility_engine import EligibilityCriteriaEngine


@pytest.fixture
def oncology_trial():
    return Trial(
        trial_id="AUDIT-TRIAL-ONC",
        trial_name="Phase III NSCLC Audit Protocol",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults with EGFR+ NSCLC",
        target_enrollment=100,
        enrollment_deadline="2027-12-31",
        inclusion_criteria=[
            EligibilityCriterion(
                criterion_id="INC-AGE-18-75",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.AGE,
                field_name="age",
                operator="between",
                target_value=[18, 75],
                description="Age between 18 and 75 years",
            ),
            EligibilityCriterion(
                criterion_id="INC-STAGE-ADV",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.DISEASE_STAGE,
                field_name="disease_stage",
                operator="in",
                target_value=["Stage IIIB", "Stage IV"],
                description="Stage IIIB or IV NSCLC",
            ),
            EligibilityCriterion(
                criterion_id="INC-EGFR-MUT",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.BIOMARKER,
                field_name="EGFR_mutation",
                operator="in",
                target_value=["Exon 19 del", "L858R"],
                description="Sensitizing EGFR mutation",
            ),
            EligibilityCriterion(
                criterion_id="INC-RENAL-EGFR",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.LAB_VALUE,
                field_name="eGFR",
                operator=">=",
                target_value=50.0,
                description="Renal function eGFR >= 50 mL/min",
            ),
            EligibilityCriterion(
                criterion_id="INC-CONSENT",
                criterion_type=CriterionType.INCLUSION,
                category=CriterionCategory.CONSENT,
                field_name="consent_status",
                operator="is_true",
                target_value=True,
                description="Signed written consent",
            ),
        ],
        exclusion_criteria=[
            EligibilityCriterion(
                criterion_id="EXC-BRAIN-METS",
                criterion_type=CriterionType.EXCLUSION,
                category=CriterionCategory.COMORBIDITY,
                field_name="comorbidities",
                operator="contains_any",
                target_value=["Untreated Brain Metastases"],
                description="Untreated brain metastases",
            ),
            EligibilityCriterion(
                criterion_id="EXC-PROHIBITED-DRUG",
                criterion_type=CriterionType.EXCLUSION,
                category=CriterionCategory.MEDICATION,
                field_name="medications",
                operator="contains_any",
                target_value=["Strong CYP3A4 Inducers"],
                description="Concurrent strong CYP3A4 inducers",
            ),
        ],
    )


def test_audit_clearly_eligible_patient(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-ELIGIBLE",
        age=52,
        sex="Female",
        region="Midwest",
        disease_stage="Stage IV",
        biomarkers={"EGFR_mutation": "L858R"},
        lab_values={"eGFR": 68.0, "platelets": 200000.0},
        medications=["Metformin"],
        comorbidities=["Hypertension"],
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.confidence >= 0.95
    assert result.requires_human_review is False
    assert len(result.matched_inclusion) == 5
    assert len(result.failed_inclusion) == 0
    assert len(result.triggered_exclusion) == 0
    assert "satisfies all" in result.explanation.lower()


def test_audit_failing_inclusion_age(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-FAIL-AGE",
        age=81,  # Fails age criteria [18, 75]
        sex="Male",
        region="Northeast",
        disease_stage="Stage IV",
        biomarkers={"EGFR_mutation": "Exon 19 del"},
        lab_values={"eGFR": 62.0},
        medications=[],
        comorbidities=[],
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.failed_inclusion) == 1
    assert "INC-AGE-18-75" in result.failed_inclusion[0]
    assert "unmet inclusion" in result.explanation.lower()


def test_audit_failing_inclusion_lab(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-FAIL-LAB",
        age=55,
        sex="Male",
        region="South",
        disease_stage="Stage IV",
        biomarkers={"EGFR_mutation": "L858R"},
        lab_values={"eGFR": 38.0},  # Threshold is >= 50.0
        medications=[],
        comorbidities=[],
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert any("INC-RENAL-EGFR" in f for f in result.failed_inclusion)
    assert "eGFR (38.0) >= 50.0: False" in result.explanation or "INC-RENAL-EGFR" in result.explanation


def test_audit_triggering_exclusion_comorbidity(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-EXC-COMORB",
        age=60,
        sex="Female",
        region="West",
        disease_stage="Stage IV",
        biomarkers={"EGFR_mutation": "Exon 19 del"},
        lab_values={"eGFR": 58.0},
        medications=[],
        comorbidities=["Untreated Brain Metastases"],  # Prohibited comorbidity!
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.triggered_exclusion) == 1
    assert "EXC-BRAIN-METS" in result.triggered_exclusion[0]
    assert "triggered exclusion" in result.explanation.lower()


def test_audit_triggering_exclusion_medication(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-EXC-MED",
        age=45,
        sex="Female",
        region="Midwest",
        disease_stage="Stage IIIB",
        biomarkers={"EGFR_mutation": "L858R"},
        lab_values={"eGFR": 72.0},
        medications=["Strong CYP3A4 Inducers", "Aspirin"],  # Prohibited med!
        comorbidities=[],
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert len(result.triggered_exclusion) == 1
    assert "EXC-PROHIBITED-DRUG" in result.triggered_exclusion[0]


def test_audit_missing_lab_triggers_uncertain_review(oncology_trial):
    engine = EligibilityCriteriaEngine()
    patient = Patient(
        synthetic_patient_id="AUDIT-PT-MISSING-EGFR",
        age=62,
        sex="Male",
        region="Pacific",
        disease_stage="Stage IV",
        biomarkers={"EGFR_mutation": "Exon 19 del"},
        lab_values={},  # eGFR is completely missing!
        medications=[],
        comorbidities=[],
        consent_status=True,
    )

    result = engine.evaluate_patient(patient, oncology_trial)
    # Must NOT claim certainty or fail patient arbitrarily
    assert result.status == EligibilityStatus.UNCERTAIN
    assert result.requires_human_review is True
    assert len(result.missing_information) == 1
    assert "eGFR" in result.missing_information[0]
    assert "UNCERTAIN" in result.explanation
    assert "Human Review" in result.explanation
    assert result.confidence < 0.80  # Penalized confidence
