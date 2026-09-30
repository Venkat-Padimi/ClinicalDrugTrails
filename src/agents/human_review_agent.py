"""Human-In-The-Loop Review Console Agent.

Provides structured human review routing, auditable decision recording,
and explicit override tracking. Never silently overrides automated findings.
"""

from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
from src.domain.models import (
    HumanReviewDecision,
    HumanDecisionType,
    ReviewItemType,
    PatientScreeningResult,
    EligibilityStatus,
    SiteRisk,
    SiteRanking,
    AuditEvent,
)
from src.audit.audit_trail import audit_logger, AuditTrail


class HumanReviewAgent:
    """Agent managing the Human Review Console and explicit decision provenance."""

    def __init__(self, audit: Optional[AuditTrail] = None):
        self.audit = audit or audit_logger
        self.decision_history: List[HumanReviewDecision] = []

    def identify_pending_reviews(
        self,
        screening_results: List[PatientScreeningResult],
        site_risks: List[SiteRisk],
        site_rankings: List[SiteRanking],
    ) -> Dict[str, List[Any]]:
        """Identifies all cohort and site items flagged for human review."""
        uncertain_patients = [r for r in screening_results if r.requires_human_review]
        flagged_risks = [r for r in site_risks if r.requires_human_review]
        flagged_rankings = [r for r in site_rankings if r.requires_review]

        return {
            "patients": uncertain_patients,
            "site_risks": flagged_risks,
            "site_rankings": flagged_rankings,
        }

    def record_patient_decision(
        self,
        patient_result: PatientScreeningResult,
        reviewer_id: str,
        decision: HumanDecisionType,
        justification_notes: str,
        override_status: Optional[EligibilityStatus] = None,
    ) -> Tuple[PatientScreeningResult, HumanReviewDecision]:
        """Applies a human review decision to an uncertain patient record."""
        rev_id = f"REV-PT-{uuid.uuid4().hex[:6].upper()}"
        overrides = {}

        original_status = patient_result.status
        updated_result = patient_result.model_copy(deep=True)

        if decision == HumanDecisionType.MODIFY and override_status is not None:
            updated_result.status = override_status
            updated_result.explanation += (
                f"\n[HUMAN OVERRIDE by {reviewer_id}]: Status modified from {original_status.value} to {override_status.value}. "
                f"Justification: {justification_notes}"
            )
            overrides["previous_status"] = original_status.value
            overrides["new_status"] = override_status.value
            updated_result.requires_human_review = False
        elif decision == HumanDecisionType.APPROVE:
            updated_result.explanation += (
                f"\n[HUMAN APPROVAL by {reviewer_id}]: Automated assessment approved as valid. Justification: {justification_notes}"
            )
            updated_result.requires_human_review = False
        elif decision == HumanDecisionType.REJECT:
            updated_result.status = EligibilityStatus.INELIGIBLE
            updated_result.explanation += (
                f"\n[HUMAN REJECTION by {reviewer_id}]: Patient disqualified from trial cohort. Justification: {justification_notes}"
            )
            overrides["disqualified"] = True
            updated_result.requires_human_review = False
        elif decision == HumanDecisionType.REQUEST_MORE_EVIDENCE:
            updated_result.explanation += (
                f"\n[EVIDENCE REQUEST by {reviewer_id}]: Additional source data verification requested. Justification: {justification_notes}"
            )
            overrides["status"] = "PENDING_ADDITIONAL_SOURCE_DATA"
            # Remains in human review

        rev_record = HumanReviewDecision(
            review_id=rev_id,
            item_type=ReviewItemType.PATIENT_ELIGIBILITY,
            item_id=patient_result.patient_id,
            reviewer_id=reviewer_id,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            justification_notes=justification_notes,
            override_values=overrides,
            applied=True,
        )
        self.decision_history.append(rev_record)

        # Audit Event
        self.audit.record_event(
            agent_or_node="HumanReviewAgent",
            action="PATIENT_ELIGIBILITY_REVIEW",
            input_summary=f"Patient {patient_result.patient_id} (Prior Status: {original_status.value})",
            output_summary=f"Decision: {decision.value}, New Status: {updated_result.status.value}",
            decision=decision.value,
            confidence=1.0,
            warnings=[f"Human override applied by {reviewer_id}"] if overrides else [],
            data_provenance="Human-In-The-Loop Console",
        )

        return updated_result, rev_record

    def record_site_decision(
        self,
        ranking_item: SiteRanking,
        reviewer_id: str,
        decision: HumanDecisionType,
        justification_notes: str,
        override_priority_score: Optional[float] = None,
    ) -> Tuple[SiteRanking, HumanReviewDecision]:
        """Applies a human review decision to a trial site ranking."""
        rev_id = f"REV-SITE-{uuid.uuid4().hex[:6].upper()}"
        overrides = {}

        updated_ranking = ranking_item.model_copy(deep=True)
        prior_score = ranking_item.priority_score

        if decision == HumanDecisionType.MODIFY and override_priority_score is not None:
            updated_ranking.priority_score = max(0.0, min(100.0, override_priority_score))
            updated_ranking.rationale += (
                f"\n[HUMAN SCORE ADJUSTMENT by {reviewer_id}]: Score adjusted from {prior_score} to {override_priority_score}. "
                f"Justification: {justification_notes}"
            )
            overrides["previous_priority_score"] = prior_score
            overrides["new_priority_score"] = override_priority_score
            updated_ranking.requires_review = False
        elif decision == HumanDecisionType.APPROVE:
            updated_ranking.rationale += (
                f"\n[HUMAN APPROVAL by {reviewer_id}]: Site priority and risk flags acknowledged and accepted."
            )
            updated_ranking.requires_review = False
        elif decision == HumanDecisionType.REJECT:
            updated_ranking.priority_score = 0.0
            updated_ranking.rationale += (
                f"\n[HUMAN DISQUALIFICATION by {reviewer_id}]: Site disqualified from trial selection. "
                f"Justification: {justification_notes}"
            )
            overrides["disqualified"] = True
            updated_ranking.requires_review = False
        elif decision == HumanDecisionType.REQUEST_MORE_EVIDENCE:
            updated_ranking.rationale += (
                f"\n[EVIDENCE REQUEST by {reviewer_id}]: Formal GCP site qualification audit requested prior to activation."
            )
            overrides["status"] = "SITE_AUDIT_REQUESTED"

        rev_record = HumanReviewDecision(
            review_id=rev_id,
            item_type=ReviewItemType.SITE_RANKING,
            item_id=ranking_item.site_id,
            reviewer_id=reviewer_id,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            justification_notes=justification_notes,
            override_values=overrides,
            applied=True,
        )
        self.decision_history.append(rev_record)

        # Audit Event
        self.audit.record_event(
            agent_or_node="HumanReviewAgent",
            action="SITE_SELECTION_REVIEW",
            input_summary=f"Site {ranking_item.site_id} (Prior Score: {prior_score})",
            output_summary=f"Decision: {decision.value}, Final Score: {updated_ranking.priority_score}",
            decision=decision.value,
            confidence=1.0,
            warnings=[f"Site ranking review submitted by {reviewer_id}"] if overrides else [],
            data_provenance="Human-In-The-Loop Console",
        )

        return updated_ranking, rev_record


human_review_agent = HumanReviewAgent()
