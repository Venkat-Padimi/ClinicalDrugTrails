"""End-to-end integration test for the Clinical Trial Agent system."""

import pytest
import json
from src.domain.models import (
    EligibilityStatus,
    HumanDecisionType,
    RiskLevel,
    TrialAnalysisResult,
)
from src.providers.synthetic_data_generator import SyntheticDataProvider
from src.workflow.orchestrator import TrialWorkflowOrchestrator
from src.agents.human_review_agent import HumanReviewAgent
from src.reporting.report_generator import ExecutiveReportGenerator
from src.audit.audit_trail import AuditTrail
from src.config import DISCLAIMER_TEXT

def test_full_pipeline_end_to_end():
    # 1. Initialize data provider & fixtures
    provider = SyntheticDataProvider(seed=777)
    trials = provider.get_trials()
    sites = provider.get_sites()
    patients = provider.generator.generate_patients(count=60, sites=sites)
    trial = trials[0]
    deviations = provider.generator.generate_deviations(sites=sites, trial_id=trial.trial_id, count=20)

    # 2. Setup orchestrator with isolated audit trail
    test_audit = AuditTrail()
    orchestrator = TrialWorkflowOrchestrator(audit=test_audit)

    # 3. Execute Multi-Agent Workflow
    result: TrialAnalysisResult = orchestrator.run(
        trial=trial,
        patients=patients,
        sites=sites,
        deviations=deviations,
    )

    # 4. Verify Pipeline Completeness
    assert result.trial.trial_id == trial.trial_id
    assert result.screening_summary.total_screened == 60
    assert len(result.patient_screening_results) == 60
    assert len(result.site_performances) == len(sites)
    assert len(result.site_risks) == len(sites)
    assert len(result.site_rankings) == len(sites)
    assert result.site_rankings[0].rank == 1
    assert result.site_rankings[0].priority_score >= result.site_rankings[-1].priority_score
    assert result.recruitment_forecast.target_enrollment == trial.target_enrollment
    assert result.deviation_summary.total_deviations == 20
    assert len(result.audit_events) >= 10

    # 5. Verify Safety Disclaimers
    assert DISCLAIMER_TEXT in result.synthetic_disclaimer or "Synthetic" in result.synthetic_disclaimer

    # 6. Test Human-in-the-Loop Review
    human_agent = HumanReviewAgent(audit=test_audit)
    pending = human_agent.identify_pending_reviews(
        result.patient_screening_results,
        result.site_risks,
        result.site_rankings,
    )

    if pending["patients"]:
        pt = pending["patients"][0]
        updated_pt, dec = human_agent.record_patient_decision(
            patient_result=pt,
            reviewer_id="MD-VERIFIER",
            decision=HumanDecisionType.MODIFY,
            justification_notes="Synthetic lab verified in range by central lab amendment.",
            override_status=EligibilityStatus.ELIGIBLE,
        )
        assert updated_pt.status == EligibilityStatus.ELIGIBLE
        assert dec.decision == HumanDecisionType.MODIFY

    if pending["site_rankings"]:
        s_rank = pending["site_rankings"][0]
        updated_s, dec = human_agent.record_site_decision(
            ranking_item=s_rank,
            reviewer_id="QA-DIRECTOR",
            decision=HumanDecisionType.APPROVE,
            justification_notes="Site audit findings resolved under approved CAPA plan.",
        )
        assert dec.decision == HumanDecisionType.APPROVE

    # 7. Test Reporting and Export
    reporter = ExecutiveReportGenerator()
    md = reporter.generate_markdown_report(result)
    assert "Executive Summary" in md
    assert "MANDATORY SAFETY DISCLAIMER" in md

    json_str = reporter.generate_json_report(result)
    loaded = json.loads(json_str)
    assert loaded["trial"]["trial_id"] == trial.trial_id

    patients_csv = reporter.generate_patients_csv(result)
    assert len(patients_csv.strip().split("\n")) == 61  # Header + 60

    sites_csv = reporter.generate_sites_csv(result)
    assert len(sites_csv.strip().split("\n")) == len(sites) + 1

    deviations_csv = reporter.generate_deviations_csv(result)
    assert len(deviations_csv.strip().split("\n")) == 21  # Header + 20

    # 8. Assert Complete 11-Node Sequence in Audit Trace
    recorded_nodes = [e.agent_or_node for e in result.audit_events]
    expected_nodes = [
        "TrialIntakeAgent",
        "CriteriaParsingAgent",
        "PatientScreeningAgent",
        "EligibilityEvidenceAgent",
        "SiteIntelligenceAgent",
        "RecruitmentForecastAgent",
        "ProtocolDeviationAgent",
        "SiteRiskAgent",
        "SiteRankingAgent",
        "ReportingAgent",
    ]
    for exp in expected_nodes:
        assert exp in recorded_nodes, f"Expected node {exp} missing from audit trail!"
