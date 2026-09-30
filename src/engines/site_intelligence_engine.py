"""Site Intelligence Engine.

Computes transparent, deterministic operational and recruitment performance scores
for clinical trial sites without LLM hallucination of numerical metrics.
"""

from typing import List, Dict, Any
from src.domain.models import TrialSite, SitePerformance


class SiteIntelligenceEngine:
    """Deterministic operational intelligence evaluator for candidate sites."""

    def evaluate_site(self, site: TrialSite) -> SitePerformance:
        """Calculates multi-dimensional performance scores for a trial site."""
        # 1. Enrollment Velocity Score (0 - 100)
        # Benchmark: 5.0 patients/month is elite (100)
        vel_score = min(100.0, (site.average_monthly_enrollment / 5.0) * 100.0)
        vel_score = max(0.0, round(vel_score, 1))

        # 2. Experience Score (0 - 100)
        # 15 years TA experience = 100%, 18 years investigator = 100%
        ta_score = min(100.0, (site.therapeutic_area_experience_years / 15.0) * 100.0)
        inv_score = min(100.0, (site.investigator_experience_years / 18.0) * 100.0)
        exp_score = max(0.0, round((0.5 * ta_score) + (0.5 * inv_score), 1))

        # 3. Compliance Score (0 - 100)
        # Inversely penalize deviation rate per 10 patients
        # Rate of 0.2 -> 94, Rate of 1.0 -> 70, Rate >= 2.5 -> < 25
        comp_score = max(0.0, min(100.0, 100.0 - (site.protocol_deviation_rate * 30.0)))
        comp_score = round(comp_score, 1)

        # 4. Data Quality Score (0 - 100)
        # Inversely penalize queries per CRF (benchmark 0.5 queries/CRF)
        dq_penalty = max(0.0, (site.data_query_rate - 0.5) / 2.5) * 60.0
        dq_score = max(0.0, min(100.0, 100.0 - dq_penalty))
        dq_score = round(dq_score, 1)

        # 5. Operational Efficiency Score (0 - 100)
        # Screen failure (0.10 baseline), dropout (0.05 baseline), activation (45 days baseline)
        sf_sub = max(0.0, min(100.0, 100.0 - ((site.screen_failure_rate - 0.10) / 0.30) * 60.0))
        do_sub = max(0.0, min(100.0, 100.0 - ((site.dropout_rate - 0.05) / 0.15) * 60.0))
        act_sub = max(0.0, min(100.0, 100.0 - ((site.activation_time_days - 45) / 75.0) * 60.0))
        ops_score = max(0.0, round((0.35 * sf_sub) + (0.35 * do_sub) + (0.30 * act_sub), 1))

        # 6. Capacity Score (0 - 100)
        # Staff coordinators (10 = 100%), Patient pool (500 = 100%)
        staff_sub = min(100.0, (site.staff_capacity / 10.0) * 100.0)
        pool_sub = min(100.0, (site.patient_pool_estimate / 500.0) * 100.0)
        cap_score = max(0.0, round((0.5 * staff_sub) + (0.5 * pool_sub), 1))

        # 7. Composite Performance Score (0 - 100)
        composite = (
            0.25 * vel_score
            + 0.20 * exp_score
            + 0.20 * comp_score
            + 0.15 * dq_score
            + 0.10 * ops_score
            + 0.10 * cap_score
        )
        composite = max(0.0, min(100.0, round(composite, 1)))

        metrics = {
            "average_monthly_enrollment": site.average_monthly_enrollment,
            "historical_trials_completed": site.historical_trials_completed,
            "historical_enrollment": site.historical_enrollment,
            "screen_failure_rate": site.screen_failure_rate,
            "dropout_rate": site.dropout_rate,
            "protocol_deviation_rate": site.protocol_deviation_rate,
            "data_query_rate": site.data_query_rate,
            "activation_time_days": site.activation_time_days,
            "staff_capacity": site.staff_capacity,
            "patient_pool_estimate": site.patient_pool_estimate,
        }

        return SitePerformance(
            site_id=site.site_id,
            site_name=site.site_name,
            enrollment_velocity_score=vel_score,
            experience_score=exp_score,
            compliance_score=comp_score,
            data_quality_score=dq_score,
            operational_efficiency_score=ops_score,
            capacity_score=cap_score,
            composite_performance_score=composite,
            metrics_summary=metrics,
        )

    def evaluate_sites(self, sites: List[TrialSite]) -> List[SitePerformance]:
        """Evaluates a collection of trial sites deterministically."""
        return [self.evaluate_site(s) for s in sites]


site_intelligence_engine = SiteIntelligenceEngine()
