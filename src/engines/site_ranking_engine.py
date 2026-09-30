"""Site Prioritization and Ranking Engine.

Performs deterministic multi-criteria decision analysis (MCDA) to rank clinical trial sites
on a 0-100 normalized priority scale with grounded strengths, weaknesses, risk flags,
and transparent rationale.
"""

from typing import List, Dict, Any, Optional
from src.domain.models import (
    TrialSite,
    SitePerformance,
    SiteRisk,
    SiteRanking,
    RiskLevel,
)
from src.config import SiteRankingWeights, config
from src.engines.site_intelligence_engine import site_intelligence_engine, SiteIntelligenceEngine
from src.engines.site_risk_engine import site_risk_engine, SiteRiskEngine


class SiteRankingEngine:
    """Deterministic Multi-Criteria Site Ranking Engine."""

    def __init__(
        self,
        weights: Optional[SiteRankingWeights] = None,
        intelligence_engine: Optional[SiteIntelligenceEngine] = None,
        risk_engine: Optional[SiteRiskEngine] = None,
    ):
        self.weights = weights or config.ranking_weights
        self.intelligence_engine = intelligence_engine or site_intelligence_engine
        self.risk_engine = risk_engine or site_risk_engine

    def rank_sites(
        self,
        sites: List[TrialSite],
        performances: Optional[List[SitePerformance]] = None,
        risks: Optional[List[SiteRisk]] = None,
    ) -> List[SiteRanking]:
        """Ranks trial sites using deterministic multi-criteria scoring."""
        if not sites:
            return []

        # If performances or risks not passed, compute deterministically
        if performances is None:
            performances = self.intelligence_engine.evaluate_sites(sites)
        if risks is None:
            risks = self.risk_engine.assess_all_sites(sites)

        perf_map = {p.site_id: p for p in performances}
        risk_map = {r.site_id: r for r in risks}

        w = self.weights
        ranked_candidates = []

        for site in sites:
            perf = perf_map.get(site.site_id)
            risk = risk_map.get(site.site_id)
            if not perf or not risk:
                continue

            # 1. Base Score (weighted multi-criteria sum, 0 - 100)
            base_score = (
                (w.recruitment_score_weight * perf.enrollment_velocity_score)
                + (w.operational_score_weight * perf.operational_efficiency_score)
                + (w.experience_score_weight * perf.experience_score)
                + (w.data_quality_weight * perf.data_quality_score)
                + (w.compliance_score_weight * perf.compliance_score)
            )

            # 2. Risk Penalty (deduct up to 25 points for high risk profiles)
            # High risk score (e.g. 70) results in (70/100)*25 = 17.5 pt penalty
            risk_penalty = (risk.overall_risk_score / 100.0) * 25.0

            # 3. Net Priority Score (clamped to 0 - 100)
            priority_score = max(0.0, min(100.0, round(base_score - risk_penalty, 1)))

            # 4. Confidence assessment
            # High trials completed + clean data quality -> high confidence
            trials_factor = min(1.0, site.historical_trials_completed / 30.0)
            dq_factor = perf.data_quality_score / 100.0
            confidence = round(min(0.98, max(0.60, 0.70 + (0.15 * trials_factor) + (0.13 * dq_factor))), 2)

            # 5. Identify Strengths
            strengths = []
            if site.average_monthly_enrollment >= 4.0:
                strengths.append(f"High enrollment velocity ({site.average_monthly_enrollment} pts/month).")
            if site.screen_failure_rate <= 0.16:
                strengths.append(f"Low screen failure rate ({round(site.screen_failure_rate * 100, 1)}%).")
            if site.investigator_experience_years >= 14.0:
                strengths.append(f"Senior investigator track record ({site.investigator_experience_years} years).")
            if perf.compliance_score >= 85.0:
                strengths.append(f"Strong protocol compliance record (score {perf.compliance_score}/100).")
            if site.activation_time_days <= 60:
                strengths.append(f"Rapid site activation capability ({site.activation_time_days} days).")
            if not strengths:
                strengths.append("Meets minimum baseline criteria for trial participation.")

            # 6. Identify Weaknesses
            weaknesses = []
            if site.average_monthly_enrollment < 2.5:
                weaknesses.append(f"Sub-optimal enrollment velocity ({site.average_monthly_enrollment} pts/month).")
            if site.dropout_rate >= 0.12:
                weaknesses.append(f"Elevated subject dropout rate ({round(site.dropout_rate * 100, 1)}%).")
            if site.data_query_rate >= 2.0:
                weaknesses.append(f"High data clarification query rate ({site.data_query_rate} queries/CRF).")
            if site.activation_time_days >= 85:
                weaknesses.append(f"Prolonged activation timeline ({site.activation_time_days} days).")
            if site.staff_capacity <= 4:
                weaknesses.append(f"Constrained clinical research coordinator staffing ({site.staff_capacity} staff).")

            # 7. Risk flags
            risk_flags = list(risk.risk_factors)

            # 8. Grounded Rationale
            rationale = (
                f"This synthetic analysis assigns site '{site.site_name}' a priority score of {priority_score}/100 "
                f"(rank determined deterministically). The site demonstrates a base operational score of {round(base_score, 1)} "
                f"with a calibrated risk deduction of {round(risk_penalty, 1)} points based on its {risk.risk_level.value} risk profile. "
                f"Projected recruitment capacity is ~{site.average_monthly_enrollment} patients/month."
            )

            requires_review = (priority_score < 50.0) or risk.requires_human_review

            ranked_candidates.append(
                SiteRanking(
                    rank=0,  # Assigned after sorting
                    site_id=site.site_id,
                    site_name=site.site_name,
                    priority_score=priority_score,
                    confidence=confidence,
                    strengths=strengths,
                    weaknesses=weaknesses,
                    risk_flags=risk_flags,
                    recruitment_estimate_monthly=site.average_monthly_enrollment,
                    rationale=rationale,
                    requires_review=requires_review,
                )
            )

        # Sort descending by priority_score
        ranked_candidates.sort(key=lambda x: x.priority_score, reverse=True)

        # Assign ranks
        for idx, item in enumerate(ranked_candidates, start=1):
            item.rank = idx

        return ranked_candidates


site_ranking_engine = SiteRankingEngine()
