"""Deterministic Eligibility Criteria Engine.

Evaluates synthetic patients against structured clinical trial criteria.
Ensures transparent, deterministic rule evaluation with explicit missing-data handling
and human review escalation for uncertain cases.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from src.domain.models import (
    Trial,
    Patient,
    EligibilityCriterion,
    CriterionType,
    CriterionCategory,
    EligibilityStatus,
    PatientScreeningResult,
)


class EligibilityCriteriaEngine:
    """Deterministic rule evaluator for trial eligibility."""

    def __init__(self, confidence_penalty_missing: float = 0.20):
        self.confidence_penalty_missing = confidence_penalty_missing

    def extract_patient_field_value(self, patient: Patient, field_name: str) -> Tuple[Any, bool]:
        """Extracts field value from patient model or nested lab/biomarker dictionaries.
        
        Returns:
            Tuple[Any, bool]: (extracted_value, exists_flag)
        """
        # Direct attributes
        if hasattr(patient, field_name):
            val = getattr(patient, field_name)
            if val is not None:
                return val, True

        # Lab values dictionary
        if field_name in patient.lab_values:
            return patient.lab_values[field_name], True

        # Biomarkers dictionary
        if field_name in patient.biomarkers:
            return patient.biomarkers[field_name], True

        # Field not found or missing
        return None, False

    def evaluate_criterion(
        self, patient: Patient, criterion: EligibilityCriterion
    ) -> Tuple[bool, bool, str]:
        """Evaluates a single criterion against a patient.
        
        Returns:
            Tuple[bool, bool, str]: (is_satisfied, is_missing, details)
        """
        val, exists = self.extract_patient_field_value(patient, criterion.field_name)

        if not exists or val is None:
            return False, True, f"Missing required data field: '{criterion.field_name}'"

        op = criterion.operator.lower().strip()
        target = criterion.target_value

        try:
            if op == ">=":
                satisfied = float(val) >= float(target)
                msg = f"{criterion.field_name} ({val}) >= {target}: {satisfied}"
            elif op == "<=":
                satisfied = float(val) <= float(target)
                msg = f"{criterion.field_name} ({val}) <= {target}: {satisfied}"
            elif op == ">":
                satisfied = float(val) > float(target)
                msg = f"{criterion.field_name} ({val}) > {target}: {satisfied}"
            elif op == "<":
                satisfied = float(val) < float(target)
                msg = f"{criterion.field_name} ({val}) < {target}: {satisfied}"
            elif op == "==":
                if isinstance(val, str) and isinstance(target, str):
                    satisfied = val.strip().lower() == target.strip().lower()
                else:
                    satisfied = val == target
                msg = f"{criterion.field_name} ({val}) == {target}: {satisfied}"
            elif op == "!=":
                if isinstance(val, str) and isinstance(target, str):
                    satisfied = val.strip().lower() != target.strip().lower()
                else:
                    satisfied = val != target
                msg = f"{criterion.field_name} ({val}) != {target}: {satisfied}"
            elif op == "between":
                lower, upper = float(target[0]), float(target[1])
                satisfied = lower <= float(val) <= upper
                msg = f"{criterion.field_name} ({val}) between [{lower}, {upper}]: {satisfied}"
            elif op == "in":
                # Checks if patient's single value is in target list
                target_norm = [str(x).strip().lower() for x in target] if isinstance(target, list) else [str(target).lower()]
                satisfied = str(val).strip().lower() in target_norm
                msg = f"{criterion.field_name} ('{val}') in {target}: {satisfied}"
            elif op == "not_in":
                target_norm = [str(x).strip().lower() for x in target] if isinstance(target, list) else [str(target).lower()]
                satisfied = str(val).strip().lower() not in target_norm
                msg = f"{criterion.field_name} ('{val}') not in {target}: {satisfied}"
            elif op == "contains_any":
                # For list-valued patient fields like medications, comorbidities, prior_treatments
                patient_list = [str(x).strip().lower() for x in val] if isinstance(val, list) else [str(val).lower()]
                target_list = [str(x).strip().lower() for x in target] if isinstance(target, list) else [str(target).lower()]
                overlap = set(patient_list).intersection(set(target_list))
                satisfied = len(overlap) > 0
                msg = f"{criterion.field_name} contains any of {target} (matched: {list(overlap)}): {satisfied}"
            elif op == "contains_all":
                patient_list = [str(x).strip().lower() for x in val] if isinstance(val, list) else [str(val).lower()]
                target_list = [str(x).strip().lower() for x in target] if isinstance(target, list) else [str(target).lower()]
                satisfied = set(target_list).issubset(set(patient_list))
                msg = f"{criterion.field_name} contains all of {target}: {satisfied}"
            elif op == "is_true":
                satisfied = bool(val) is True
                msg = f"{criterion.field_name} is True: {satisfied}"
            elif op == "exists":
                satisfied = val is not None and val != ""
                msg = f"{criterion.field_name} exists: {satisfied}"
            else:
                return False, False, f"Unsupported operator: {op}"

            return satisfied, False, msg
        except Exception as e:
            return False, False, f"Evaluation error on '{criterion.field_name}': {str(e)}"

    def evaluate_patient(self, patient: Patient, trial: Trial) -> PatientScreeningResult:
        """Determines patient eligibility against all inclusion and exclusion criteria."""
        matched_inclusion = []
        failed_inclusion = []
        triggered_exclusion = []
        missing_information = []
        explanation_lines = []

        # 1. Evaluate Inclusion Criteria
        for crit in trial.inclusion_criteria:
            satisfied, is_missing, details = self.evaluate_criterion(patient, crit)
            if is_missing:
                missing_information.append(f"Inclusion: {crit.description} ({details})")
            elif satisfied:
                matched_inclusion.append(crit.criterion_id)
            else:
                failed_inclusion.append(f"{crit.criterion_id}: {crit.description} ({details})")

        # 2. Evaluate Exclusion Criteria
        for crit in trial.exclusion_criteria:
            satisfied, is_missing, details = self.evaluate_criterion(patient, crit)
            if is_missing:
                missing_information.append(f"Exclusion: {crit.description} ({details})")
            elif satisfied:
                # In an exclusion criterion, if the condition is met (e.g. has prohibited med), exclusion is triggered!
                triggered_exclusion.append(f"{crit.criterion_id}: {crit.description} ({details})")

        # 3. Determine Eligibility Status
        has_triggered_exclusion = len(triggered_exclusion) > 0
        has_failed_inclusion = len(failed_inclusion) > 0
        has_missing = len(missing_information) > 0

        if has_triggered_exclusion:
            status = EligibilityStatus.INELIGIBLE
            confidence = 0.95
            explanation_lines.append(f"Patient is INELIGIBLE due to {len(triggered_exclusion)} triggered exclusion criteria.")
            for exc in triggered_exclusion:
                explanation_lines.append(f" - [Triggered Exclusion] {exc}")
        elif has_failed_inclusion:
            status = EligibilityStatus.INELIGIBLE
            confidence = 0.95
            explanation_lines.append(f"Patient is INELIGIBLE due to {len(failed_inclusion)} unmet inclusion criteria.")
            for fail in failed_inclusion:
                explanation_lines.append(f" - [Failed Inclusion] {fail}")
        elif has_missing:
            # All tested criteria passed, but critical required fields were missing
            status = EligibilityStatus.UNCERTAIN
            confidence = max(0.50, 0.90 - (len(missing_information) * self.confidence_penalty_missing))
            explanation_lines.append(
                f"Patient eligibility is UNCERTAIN due to {len(missing_information)} missing clinical data point(s). "
                "Escalated to Human Review for confirmatory documentation."
            )
            for miss in missing_information:
                explanation_lines.append(f" - [Missing Field] {miss}")
        else:
            status = EligibilityStatus.ELIGIBLE
            confidence = 0.98
            explanation_lines.append(
                f"Patient satisfies all {len(matched_inclusion)} mandatory inclusion criteria "
                "with zero triggered exclusions and complete clinical data."
            )

        requires_review = (status == EligibilityStatus.UNCERTAIN) or (confidence < 0.80)
        explanation = "\n".join(explanation_lines)

        return PatientScreeningResult(
            patient_id=patient.synthetic_patient_id,
            status=status,
            confidence=confidence,
            matched_inclusion=matched_inclusion,
            failed_inclusion=failed_inclusion,
            triggered_exclusion=triggered_exclusion,
            missing_information=missing_information,
            explanation=explanation,
            requires_human_review=requires_review,
        )


eligibility_engine = EligibilityCriteriaEngine()
