"""Unit tests for HumanReviewAgent."""

import pytest
from src.domain.models import (
    PatientScreeningResult,
    EligibilityStatus,
    SiteRanking,
    HumanDecisionType,
    ReviewItemType,
)
from src.agents.human_review_agent import HumanReviewAgent
from src.audit.audit_trail import AuditTrail

def test_human_review_patient_override():
    audit = AuditTrail()
    agent = HumanReviewAgent(audit=audit)

    pt_result = PatientScreeningResult(
        patient_id="PT-UNCERTAIN-01",
        status=EligibilityStatus.UNCERTAIN,
        confidence=0.60,
        explanation="Borderline lab value",
        requires_human_review=True,
    )

    # Approve override to ELIGIBLE
    updated, decision = agent.record_patient_decision(
        patient_result=pt_result,
        reviewer_id="DR-SMITH",
        decision=HumanDecisionType.MODIFY,
        justification_notes="Secondary confirmatory lab confirms acceptable renal threshold.",
        override_status=EligibilityStatus.ELIGIBLE,
    )

    assert updated.status == EligibilityStatus.ELIGIBLE
    assert updated.requires_human_review is False
    assert "HUMAN OVERRIDE" in updated.explanation
    assert decision.item_id == "PT-UNCERTAIN-01"
    assert decision.decision == HumanDecisionType.MODIFY
    assert decision.override_values["previous_status"] == "UNCERTAIN"
    assert decision.override_values["new_status"] == "ELIGIBLE"

    # Audit event should be recorded
    events = audit.get_events()
    assert len(events) == 1
    assert events[0].agent_or_node == "HumanReviewAgent"

def test_human_review_patient_approve_and_reject():
    audit = AuditTrail()
    agent = HumanReviewAgent(audit=audit)

    pt_result = PatientScreeningResult(
        patient_id="PT-UNCERTAIN-02",
        status=EligibilityStatus.UNCERTAIN,
        confidence=0.65,
        explanation="Missing historical CBC panel",
        requires_human_review=True,
    )

    # 1. Test APPROVE
    updated_app, dec_app = agent.record_patient_decision(
        patient_result=pt_result,
        reviewer_id="MD-CHIEF-1",
        decision=HumanDecisionType.APPROVE,
        justification_notes="Protocol waiver issued due to stable alternate chemistry.",
    )
    assert dec_app.decision == HumanDecisionType.APPROVE
    assert "HUMAN APPROVAL by MD-CHIEF-1" in updated_app.explanation
    assert "Missing historical CBC panel" in updated_app.explanation  # Original preserved!
    assert updated_app.requires_human_review is False

    # 2. Test REJECT
    updated_rej, dec_rej = agent.record_patient_decision(
        patient_result=pt_result,
        reviewer_id="MD-CHIEF-1",
        decision=HumanDecisionType.REJECT,
        justification_notes="Severe comorbidity deemed unacceptable safety risk.",
    )
    assert dec_rej.decision == HumanDecisionType.REJECT
    assert updated_rej.status == EligibilityStatus.INELIGIBLE
    assert "HUMAN REJECTION by MD-CHIEF-1" in updated_rej.explanation
    assert dec_rej.override_values["disqualified"] is True


def test_human_review_site_decision():
    audit = AuditTrail()
    agent = HumanReviewAgent(audit=audit)

    site_ranking = SiteRanking(
        rank=5,
        site_id="SITE-FLAGGED",
        site_name="Flagged Site",
        priority_score=45.0,
        confidence=0.80,
        strengths=["Good location"],
        weaknesses=["High deviations"],
        risk_flags=["Critical deviation on record"],
        recruitment_estimate_monthly=2.0,
        rationale="Preliminary ranking",
        requires_review=True,
    )

    # 1. Test REQUEST_MORE_EVIDENCE
    updated, decision = agent.record_site_decision(
        ranking_item=site_ranking,
        reviewer_id="QA-DIRECTOR-1",
        decision=HumanDecisionType.REQUEST_MORE_EVIDENCE,
        justification_notes="Triggered GCP site qualification audit prior to study commitment.",
    )

    assert decision.decision == HumanDecisionType.REQUEST_MORE_EVIDENCE
    assert "GCP site qualification" in updated.rationale
    assert decision.item_type == ReviewItemType.SITE_RANKING

    # 2. Test MODIFY score
    updated_mod, dec_mod = agent.record_site_decision(
        ranking_item=site_ranking,
        reviewer_id="VP-CLINICAL",
        decision=HumanDecisionType.MODIFY,
        justification_notes="Risk mitigations committed; upgrade priority.",
        override_priority_score=68.0,
    )
    assert updated_mod.priority_score == 68.0
    assert dec_mod.override_values["previous_priority_score"] == 45.0
    assert dec_mod.override_values["new_priority_score"] == 68.0
    assert "HUMAN SCORE ADJUSTMENT" in updated_mod.rationale

    # 3. Test REJECT site
    updated_disq, dec_disq = agent.record_site_decision(
        ranking_item=site_ranking,
        reviewer_id="VP-CLINICAL",
        decision=HumanDecisionType.REJECT,
        justification_notes="Site lacks sufficient PI commitment.",
    )
    assert updated_disq.priority_score == 0.0
    assert "HUMAN DISQUALIFICATION" in updated_disq.rationale
    assert dec_disq.override_values["disqualified"] is True
