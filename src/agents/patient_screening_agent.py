"""Patient Recruitment Screening Agent.

Orchestrates population-level cohort screening against trial criteria,
aggregates screening metrics, computes exclusion distributions, and categorizes
patients into recruitable, uncertain, and ineligible cohorts.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
from src.domain.models import (
    Trial,
    Patient,
    PatientScreeningResult,
    EligibilityStatus,
    PatientScreeningSummary,
)
from src.engines.eligibility_engine import eligibility_engine, EligibilityCriteriaEngine


class PatientScreeningAgent:
    """Agent managing patient cohort screening and recruitment pool metrics."""

    def __init__(self, engine: EligibilityCriteriaEngine = None):
        self.engine = engine or eligibility_engine

    def screen_cohort(
        self, trial: Trial, patients: List[Patient]
    ) -> Tuple[List[PatientScreeningResult], PatientScreeningSummary]:
        """Screens a patient cohort against a trial and calculates aggregate metrics."""
        results: List[PatientScreeningResult] = []
        exclusion_counter: Counter = Counter()
        failed_inclusion_counter: Counter = Counter()
        missing_data_count = 0

        for patient in patients:
            res = self.engine.evaluate_patient(patient, trial)
            results.append(res)

            if res.missing_information:
                missing_data_count += 1

            for exc in res.triggered_exclusion:
                # Use criterion id as key
                crit_key = exc.split(":")[0].strip() if ":" in exc else exc
                exclusion_counter[crit_key] += 1

            for fail in res.failed_inclusion:
                crit_key = fail.split(":")[0].strip() if ":" in fail else fail
                failed_inclusion_counter[crit_key] += 1

        total = len(patients)
        eligible_count = sum(1 for r in results if r.status == EligibilityStatus.ELIGIBLE)
        ineligible_count = sum(1 for r in results if r.status == EligibilityStatus.INELIGIBLE)
        uncertain_count = sum(1 for r in results if r.status == EligibilityStatus.UNCERTAIN)

        eligibility_rate = round(eligible_count / max(1, total), 4)
        uncertain_rate = round(uncertain_count / max(1, total), 4)
        missing_rate = round(missing_data_count / max(1, total), 4)

        summary = PatientScreeningSummary(
            total_screened=total,
            eligible_count=eligible_count,
            ineligible_count=ineligible_count,
            uncertain_count=uncertain_count,
            eligibility_rate=eligibility_rate,
            uncertain_rate=uncertain_rate,
            missing_data_count=missing_data_count,
            missing_data_rate=missing_rate,
            top_exclusion_reasons=dict(exclusion_counter.most_common(10)),
            top_failed_inclusion_reasons=dict(failed_inclusion_counter.most_common(10)),
        )

        return results, summary

    def get_candidate_breakdown_by_site(
        self, patients: List[Patient], results: List[PatientScreeningResult]
    ) -> Dict[str, Dict[str, int]]:
        """Aggregates eligibility outcomes grouped by assigned trial site."""
        site_map = {p.synthetic_patient_id: p.assigned_site_id for p in patients}
        breakdown: Dict[str, Dict[str, int]] = {}

        for res in results:
            site_id = site_map.get(res.patient_id, "UNASSIGNED")
            if site_id not in breakdown:
                breakdown[site_id] = {
                    "total": 0,
                    "eligible": 0,
                    "ineligible": 0,
                    "uncertain": 0,
                }
            breakdown[site_id]["total"] += 1
            if res.status == EligibilityStatus.ELIGIBLE:
                breakdown[site_id]["eligible"] += 1
            elif res.status == EligibilityStatus.INELIGIBLE:
                breakdown[site_id]["ineligible"] += 1
            else:
                breakdown[site_id]["uncertain"] += 1

        return breakdown

    def get_geographic_distribution(
        self, patients: List[Patient], results: List[PatientScreeningResult]
    ) -> Dict[str, Dict[str, int]]:
        """Aggregates eligible pool by patient geographical region."""
        region_map = {p.synthetic_patient_id: p.region for p in patients}
        geo: Dict[str, Dict[str, int]] = {}

        for res in results:
            reg = region_map.get(res.patient_id, "Unknown")
            if reg not in geo:
                geo[reg] = {"screened": 0, "eligible": 0, "uncertain": 0}
            geo[reg]["screened"] += 1
            if res.status == EligibilityStatus.ELIGIBLE:
                geo[reg]["eligible"] += 1
            elif res.status == EligibilityStatus.UNCERTAIN:
                geo[reg]["uncertain"] += 1

        return geo


patient_screening_agent = PatientScreeningAgent()
