"""Unit tests for Multi-Agent LangGraph Workflow Orchestrator."""

import pytest
from src.providers.synthetic_data_generator import SyntheticDataGenerator
from src.workflow.orchestrator import TrialWorkflowOrchestrator
from src.audit.audit_trail import AuditTrail
from src.domain.models import TrialAnalysisResult

def test_workflow_orchestrator_execution():
    gen = SyntheticDataGenerator(seed=42)
    trials = gen.generate_trials()
    trial = trials[0]
    sites = gen.generate_sites()[:5]  # 5 sites for quick test
    patients = gen.generate_patients(count=40, sites=sites)
    deviations = gen.generate_deviations(sites=sites, count=15)

    test_audit = AuditTrail()
    orchestrator = TrialWorkflowOrchestrator(audit=test_audit)

    result = orchestrator.run(trial, patients, sites, deviations)

    assert isinstance(result, TrialAnalysisResult)
    assert result.trial.trial_id == trial.trial_id
    assert result.screening_summary.total_screened == 40
    assert len(result.site_performances) == 5
    assert len(result.site_risks) == 5
    assert len(result.site_rankings) == 5
    assert result.site_rankings[0].rank == 1
    assert result.recruitment_forecast is not None
    assert result.deviation_summary.total_deviations == 15
    assert len(result.audit_events) > 5
    assert "Synthetic" in result.synthetic_disclaimer

    # Verify audit events include nodes
    agent_names = [e.agent_or_node for e in result.audit_events]
    assert "TrialIntakeAgent" in agent_names
    assert "PatientScreeningAgent" in agent_names
    assert "SiteRankingAgent" in agent_names
    assert "ReportingAgent" in agent_names
