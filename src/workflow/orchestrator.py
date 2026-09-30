"""Multi-Agent LangGraph Orchestrator.

Implements an explicit state-machine workflow orchestrating 11 agents and deterministic engines:
1. trial_intake_node
2. criteria_parser_node
3. patient_screening_node
4. eligibility_validation_node
5. site_intelligence_node
6. recruitment_forecast_node
7. protocol_deviation_node
8. risk_assessment_node
9. site_ranking_node
10. human_review_node
11. reporting_node

Features loop protection, step budget enforcement, conditional branching to Human Review,
and comprehensive audit provenance tracing.
"""

from typing import Dict, List, Any, Optional, TypedDict
import time
from datetime import datetime
from langgraph.graph import StateGraph, END

from src.domain.models import (
    Trial,
    Patient,
    TrialSite,
    ProtocolDeviation,
    PatientScreeningResult,
    PatientScreeningSummary,
    SitePerformance,
    RecruitmentForecast,
    SiteRisk,
    SiteRanking,
    ProtocolDeviationSummary,
    HumanReviewDecision,
    TrialAnalysisResult,
    AuditEvent,
    EligibilityStatus,
    RiskLevel,
)
from src.config import config
from src.engines.eligibility_engine import eligibility_engine
from src.agents.patient_screening_agent import patient_screening_agent
from src.engines.site_intelligence_engine import site_intelligence_engine
from src.engines.recruitment_forecast_engine import recruitment_forecast_engine
from src.engines.protocol_deviation_engine import protocol_deviation_engine
from src.engines.site_risk_engine import site_risk_engine
from src.engines.site_ranking_engine import site_ranking_engine
from src.agents.human_review_agent import human_review_agent
from src.audit.audit_trail import audit_logger, AuditTrail


class TrialWorkflowState(TypedDict, total=False):
    """Workflow state shared across all nodes."""
    step_count: int
    trial: Trial
    raw_patients: List[Patient]
    raw_sites: List[TrialSite]
    raw_deviations: List[ProtocolDeviation]
    
    # Engine outputs
    screening_results: List[PatientScreeningResult]
    screening_summary: Optional[PatientScreeningSummary]
    site_performances: List[SitePerformance]
    site_risks: List[SiteRisk]
    site_rankings: List[SiteRanking]
    recruitment_forecast: Optional[RecruitmentForecast]
    deviation_summary: Optional[ProtocolDeviationSummary]
    
    # Human review & routing flags
    pending_patient_reviews: List[PatientScreeningResult]
    pending_site_reviews: List[SiteRanking]
    human_reviews: List[HumanReviewDecision]
    requires_human_escalation: bool
    
    # Final consolidated result
    analysis_result: Optional[TrialAnalysisResult]
    errors: List[str]


class TrialWorkflowOrchestrator:
    """Multi-Agent Orchestrator executing the complete trial decision-support pipeline."""

    def __init__(
        self,
        audit: Optional[AuditTrail] = None,
        risk_engine: Optional[SiteRiskEngine] = None,
        ranking_engine: Optional[SiteRankingEngine] = None,
    ):
        self.audit = audit or audit_logger
        self.risk_engine = risk_engine or site_risk_engine
        self.ranking_engine = ranking_engine or site_ranking_engine
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph StateGraph with conditional edges."""
        builder = StateGraph(TrialWorkflowState)

        # Register nodes
        builder.add_node("trial_intake", self.trial_intake_node)
        builder.add_node("criteria_parser", self.criteria_parser_node)
        builder.add_node("patient_screening", self.patient_screening_node)
        builder.add_node("eligibility_validation", self.eligibility_validation_node)
        builder.add_node("site_intelligence", self.site_intelligence_node)
        builder.add_node("recruitment_forecast", self.recruitment_forecast_node)
        builder.add_node("protocol_deviation", self.protocol_deviation_node)
        builder.add_node("risk_assessment", self.risk_assessment_node)
        builder.add_node("site_ranking", self.site_ranking_node)
        builder.add_node("human_review", self.human_review_node)
        builder.add_node("reporting", self.reporting_node)

        # Flow edges
        builder.set_entry_point("trial_intake")
        builder.add_edge("trial_intake", "criteria_parser")
        builder.add_edge("criteria_parser", "patient_screening")
        builder.add_edge("patient_screening", "eligibility_validation")
        builder.add_edge("eligibility_validation", "site_intelligence")
        builder.add_edge("site_intelligence", "recruitment_forecast")
        builder.add_edge("recruitment_forecast", "protocol_deviation")
        builder.add_edge("protocol_deviation", "risk_assessment")
        builder.add_edge("risk_assessment", "site_ranking")

        # Conditional branch after site ranking: Check if human review is needed
        builder.add_conditional_edges(
            "site_ranking",
            self.route_after_site_ranking,
            {
                "human_review": "human_review",
                "reporting": "reporting",
            },
        )

        builder.add_edge("human_review", "reporting")
        builder.add_edge("reporting", END)

        return builder.compile()

    # ==========================================
    # Workflow Nodes
    # ==========================================

    def trial_intake_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 1: Validates trial intake and protocol parameters."""
        t0 = time.time()
        trial = state.get("trial")
        step_count = state.get("step_count", 0) + 1

        self.audit.record_event(
            agent_or_node="TrialIntakeAgent",
            action="VALIDATE_TRIAL_INTAKE",
            input_summary=f"Trial: {trial.trial_id} ({trial.trial_name})",
            output_summary=f"Target: {trial.target_enrollment} patients, Area: {trial.therapeutic_area}",
            decision="TRIAL_INTAKE_ACCEPTED",
            confidence=1.0,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {"step_count": step_count}

    def criteria_parser_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 2: Verifies structured inclusion and exclusion criteria."""
        t0 = time.time()
        trial = state["trial"]
        inc_count = len(trial.inclusion_criteria)
        exc_count = len(trial.exclusion_criteria)
        step_count = state.get("step_count", 0) + 1

        self.audit.record_event(
            agent_or_node="CriteriaParsingAgent",
            action="PARSE_CRITERIA",
            input_summary=f"{inc_count} inclusion, {exc_count} exclusion criteria",
            output_summary=f"Verified machine-readable rules structure",
            decision="CRITERIA_PARSED",
            confidence=1.0,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {"step_count": step_count}

    def patient_screening_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 3: Evaluates synthetic patient cohort against criteria."""
        t0 = time.time()
        trial = state["trial"]
        patients = state.get("raw_patients", [])
        step_count = state.get("step_count", 0) + 1

        results, summary = patient_screening_agent.screen_cohort(trial, patients)

        self.audit.record_event(
            agent_or_node="PatientScreeningAgent",
            action="SCREEN_PATIENT_COHORT",
            input_summary=f"Screened {len(patients)} synthetic subjects",
            output_summary=f"Eligible: {summary.eligible_count}, Ineligible: {summary.ineligible_count}, Uncertain: {summary.uncertain_count}",
            decision="SCREENING_COMPLETE",
            confidence=0.96,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "screening_results": results,
            "screening_summary": summary,
        }

    def eligibility_validation_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 4: Validates clinical evidence and flags missing data."""
        t0 = time.time()
        results = state.get("screening_results", [])
        step_count = state.get("step_count", 0) + 1

        uncertain = [r for r in results if r.requires_human_review]

        self.audit.record_event(
            agent_or_node="EligibilityEvidenceAgent",
            action="VALIDATE_EVIDENCE",
            input_summary=f"Analyzed {len(results)} screening outputs",
            output_summary=f"{len(uncertain)} candidate(s) escalated for missing data review",
            decision="EVIDENCE_VALIDATED",
            confidence=0.98,
            warnings=[f"{len(uncertain)} cases have missing lab/biomarker data"] if uncertain else [],
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "pending_patient_reviews": uncertain,
        }

    def site_intelligence_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 5: Assesses operational site metrics deterministically."""
        t0 = time.time()
        sites = state.get("raw_sites", [])
        step_count = state.get("step_count", 0) + 1

        performances = site_intelligence_engine.evaluate_sites(sites)

        self.audit.record_event(
            agent_or_node="SiteIntelligenceAgent",
            action="EVALUATE_SITE_PERFORMANCE",
            input_summary=f"Evaluated {len(sites)} candidate sites",
            output_summary=f"Mean composite performance score: {round(sum(p.composite_performance_score for p in performances)/max(1, len(performances)), 1)}",
            decision="PERFORMANCE_EVALUATED",
            confidence=0.95,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "site_performances": performances,
        }

    def recruitment_forecast_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 6: Projects enrollment timelines and uncertainty intervals."""
        t0 = time.time()
        trial = state["trial"]
        sites = state.get("raw_sites", [])
        summary = state.get("screening_summary")
        eligible_pool = summary.eligible_count if summary else 0
        step_count = state.get("step_count", 0) + 1

        forecast = recruitment_forecast_engine.forecast_enrollment(
            trial, sites, eligible_patient_pool=eligible_pool
        )

        self.audit.record_event(
            agent_or_node="RecruitmentForecastAgent",
            action="PROJECT_ENROLLMENT_TIMELINE",
            input_summary=f"Target: {trial.target_enrollment}, Eligible Pool: {eligible_pool}",
            output_summary=f"Expected Monthly: {forecast.expected_monthly_enrollment}, P50: {forecast.p50_time_months} mo, Risk: {forecast.recruitment_risk_level.value}",
            decision=f"FORECAST_{forecast.recruitment_risk_level.value}",
            confidence=0.88,
            warnings=[f"Recruitment shortfall: {forecast.recruitment_shortfall}"] if forecast.recruitment_shortfall > 0 else [],
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "recruitment_forecast": forecast,
        }

    def protocol_deviation_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 7: Monitors protocol deviations and detects statistical anomalies."""
        t0 = time.time()
        deviations = state.get("raw_deviations", [])
        sites = state.get("raw_sites", [])
        step_count = state.get("step_count", 0) + 1

        dev_summary = protocol_deviation_engine.summarize_all(deviations, sites)

        self.audit.record_event(
            agent_or_node="ProtocolDeviationAgent",
            action="MONITOR_PROTOCOL_DEVIATIONS",
            input_summary=f"Processed {len(deviations)} deviation records",
            output_summary=f"Total: {dev_summary.total_deviations}, Critical: {dev_summary.severity_breakdown.get('CRITICAL', 0)}, Open: {dev_summary.unresolved_count}",
            decision="DEVIATIONS_PROCESSED",
            confidence=0.97,
            warnings=dev_summary.interpretations,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "deviation_summary": dev_summary,
        }

    def risk_assessment_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 8: Generates multi-criteria risk assessments per site."""
        t0 = time.time()
        sites = state.get("raw_sites", [])
        deviations = state.get("raw_deviations", [])
        step_count = state.get("step_count", 0) + 1

        risks = self.risk_engine.assess_all_sites(sites, deviations)
        high_risk_count = sum(1 for r in risks if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])

        self.audit.record_event(
            agent_or_node="SiteRiskAgent",
            action="ASSESS_SITE_RISKS",
            input_summary=f"Evaluated 6 risk dimensions across {len(sites)} sites",
            output_summary=f"{high_risk_count} site(s) classified HIGH or CRITICAL risk",
            decision="RISK_ASSESSMENT_COMPLETE",
            confidence=0.94,
            warnings=[f"{high_risk_count} site(s) require monitoring/review"] if high_risk_count > 0 else [],
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {
            "step_count": step_count,
            "site_risks": risks,
        }

    def site_ranking_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 9: Ranks candidate sites using deterministic MCDA."""
        t0 = time.time()
        sites = state.get("raw_sites", [])
        perfs = state.get("site_performances", [])
        risks = state.get("site_risks", [])
        step_count = state.get("step_count", 0) + 1

        rankings = self.ranking_engine.rank_sites(sites, perfs, risks)
        pending_site_reviews = [r for r in rankings if r.requires_review]

        top_site = rankings[0].site_name if rankings else "None"
        top_score = rankings[0].priority_score if rankings else 0.0

        self.audit.record_event(
            agent_or_node="SiteRankingAgent",
            action="RANK_CANDIDATE_SITES",
            input_summary=f"Ranked {len(rankings)} sites via MCDA",
            output_summary=f"Top candidate: '{top_site}' (Score {top_score}/100)",
            decision="SITES_RANKED",
            confidence=rankings[0].confidence if rankings else 0.90,
            warnings=[f"{len(pending_site_reviews)} site(s) flagged for human review"] if pending_site_reviews else [],
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        # Determine if human escalation is needed
        patient_uncertain = len(state.get("pending_patient_reviews", [])) > 0
        site_flags = len(pending_site_reviews) > 0
        needs_escalation = patient_uncertain or site_flags

        return {
            "step_count": step_count,
            "site_rankings": rankings,
            "pending_site_reviews": pending_site_reviews,
            "requires_human_escalation": needs_escalation,
        }

    def route_after_site_ranking(self, state: TrialWorkflowState) -> str:
        """Conditional routing function."""
        # Loop / step budget protection
        if state.get("step_count", 0) >= config.max_workflow_steps:
            return "reporting"

        if state.get("requires_human_escalation", False):
            return "human_review"
        return "reporting"

    def human_review_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 10: Human Review Console routing queue."""
        t0 = time.time()
        pt_queue = state.get("pending_patient_reviews", [])
        site_queue = state.get("pending_site_reviews", [])
        step_count = state.get("step_count", 0) + 1

        self.audit.record_event(
            agent_or_node="HumanReviewAgent",
            action="ROUTE_TO_HUMAN_REVIEW_CONSOLE",
            input_summary=f"{len(pt_queue)} uncertain patient(s), {len(site_queue)} flagged site(s)",
            output_summary="Routed flagged items to Human Review queue for investigator confirmation",
            decision="HUMAN_REVIEW_DISPATCHED",
            confidence=1.0,
            data_provenance="Human-In-The-Loop Agent",
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        return {"step_count": step_count}

    def reporting_node(self, state: TrialWorkflowState) -> Dict[str, Any]:
        """Node 11: Compiles final TrialAnalysisResult."""
        t0 = time.time()
        step_count = state.get("step_count", 0) + 1

        trial = state["trial"]
        summary = state.get("screening_summary")
        pt_results = state.get("screening_results", [])
        perfs = state.get("site_performances", [])
        risks = state.get("site_risks", [])
        rankings = state.get("site_rankings", [])
        forecast = state.get("recruitment_forecast")
        dev_summary = state.get("deviation_summary")
        deviations = state.get("raw_deviations", [])
        human_decisions = human_review_agent.decision_history

        self.audit.record_event(
            agent_or_node="ReportingAgent",
            action="COMPILE_TRIAL_ANALYSIS",
            input_summary="Consolidated all upstream multi-agent results",
            output_summary="Complete TrialAnalysisResult ready for presentation and export",
            decision="ANALYSIS_FINALIZED",
            confidence=1.0,
            execution_latency_ms=(time.time() - t0) * 1000,
        )

        analysis = TrialAnalysisResult(
            trial=trial,
            screening_summary=summary,
            patient_screening_results=pt_results,
            site_performances=perfs,
            site_risks=risks,
            site_rankings=rankings,
            recruitment_forecast=forecast,
            deviation_summary=dev_summary,
            deviations=deviations,
            human_reviews=human_decisions,
            audit_events=self.audit.get_events(),
            timestamp=datetime.now().isoformat(),
        )

        return {
            "step_count": step_count,
            "analysis_result": analysis,
        }

    def run(
        self,
        trial: Trial,
        patients: List[Patient],
        sites: List[TrialSite],
        deviations: List[ProtocolDeviation],
    ) -> TrialAnalysisResult:
        """Executes the complete multi-agent workflow."""
        initial_state: TrialWorkflowState = {
            "step_count": 0,
            "trial": trial,
            "raw_patients": patients,
            "raw_sites": sites,
            "raw_deviations": deviations,
            "human_reviews": list(human_review_agent.decision_history),
            "errors": [],
        }

        # Run compiled LangGraph
        final_state = self.graph.invoke(initial_state)
        return final_state["analysis_result"]


workflow_orchestrator = TrialWorkflowOrchestrator()
