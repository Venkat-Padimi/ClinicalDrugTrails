"""Site Risk Engine.

Evaluates multi-dimensional risk profiles across recruitment, operations, compliance,
data quality, capacity, and activation using configurable deterministic weighting.
Never obscures formulas and outputs clear mathematical breakdowns.
"""

from typing import List, Dict, Any, Optional
from src.domain.models import (
    TrialSite,
    ProtocolDeviation,
    SiteRisk,
    RiskLevel,
)
from src.config import RiskScoringWeights, config
from src.engines.protocol_deviation_engine import protocol_deviation_engine, ProtocolDeviationEngine


class SiteRiskEngine:
    """Deterministic multi-dimensional risk assessment engine for trial sites."""

    def __init__(
        self,
        weights: Optional[RiskScoringWeights] = None,
        deviation_engine: Optional[ProtocolDeviationEngine] = None,
    ):
        self.weights = weights or config.risk_weights
        self.deviation_engine = deviation_engine or protocol_deviation_engine

    def assess_site_risk(
        self, site: TrialSite, deviations: List[ProtocolDeviation] = None
    ) -> SiteRisk:
        """Calculates multi-dimensional risk scores and mathematical breakdown."""
        deviations = deviations or []
        dev_analysis = self.deviation_engine.analyze_site_deviations(
            site.site_id, site.site_name, deviations
        )

        # 1. Recruitment Risk (0 - 100)
        # Benchmark: 5.0 pts/mo is zero risk, < 1.5 is high risk; SF rate > 0.25 increases risk
        vel_risk = max(0.0, min(100.0, 100.0 - (site.average_monthly_enrollment / 5.0) * 100.0))
        sf_risk = max(0.0, min(100.0, (site.screen_failure_rate / 0.35) * 100.0))
        recruitment_risk = round((0.6 * vel_risk) + (0.4 * sf_risk), 1)

        # 2. Operational Risk (0 - 100)
        # Benchmark: dropout rate (0.20 = 100% risk), startup delay (30 days = 100% risk)
        do_risk = min(100.0, (site.dropout_rate / 0.18) * 100.0)
        delay_risk = min(100.0, (site.recruitment_start_delay_days / 28.0) * 100.0)
        operational_risk = round((0.55 * do_risk) + (0.45 * delay_risk), 1)

        # 3. Compliance Risk (0 - 100)
        # Deviation risk score combined with historical deviation rate
        hist_dev_risk = min(100.0, (site.protocol_deviation_rate / 2.0) * 100.0)
        current_dev_risk = dev_analysis["deviation_risk_score"]
        compliance_risk = round((0.65 * current_dev_risk) + (0.35 * hist_dev_risk), 1)

        # 4. Data Quality Risk (0 - 100)
        # 0.5 queries/CRF = 0% risk; 3.0 queries/CRF = 100% risk
        dq_risk = max(0.0, min(100.0, ((site.data_query_rate - 0.5) / 2.2) * 100.0))
        data_quality_risk = round(dq_risk, 1)

        # 5. Experience Risk (0 - 100)
        inv_exp_risk = max(0.0, min(100.0, 100.0 - (site.investigator_experience_years / 18.0) * 100.0))
        ta_exp_risk = max(0.0, min(100.0, 100.0 - (site.therapeutic_area_experience_years / 15.0) * 100.0))
        experience_risk = round((0.5 * inv_exp_risk) + (0.5 * ta_exp_risk), 1)

        # 6. Capacity Risk (0 - 100)
        staff_risk = max(0.0, min(100.0, 100.0 - (site.staff_capacity / 8.0) * 100.0))
        pool_risk = max(0.0, min(100.0, 100.0 - (site.patient_pool_estimate / 450.0) * 100.0))
        capacity_risk = round((0.5 * staff_risk) + (0.5 * pool_risk), 1)

        # 7. Activation Risk (0 - 100)
        # 45 days = 0 risk, 110 days = 100% risk
        act_risk = max(0.0, min(100.0, ((site.activation_time_days - 45) / 65.0) * 100.0))
        activation_risk = round(act_risk, 1)

        # Combined Capacity & Activation sub-score
        cap_act_combined = (0.5 * capacity_risk) + (0.5 * activation_risk)

        # Normalize weights so sum is 1.0 regardless of slider adjustments
        w = self.weights
        w_sum = (
            w.recruitment_weight
            + w.compliance_weight
            + w.data_quality_weight
            + w.investigator_experience_weight
            + w.operational_weight
            + w.capacity_activation_weight
        )
        norm_factor = 1.0 / max(1e-6, w_sum)
        rec_w = round(w.recruitment_weight * norm_factor, 4)
        comp_w = round(w.compliance_weight * norm_factor, 4)
        dq_w = round(w.data_quality_weight * norm_factor, 4)
        exp_w = round(w.investigator_experience_weight * norm_factor, 4)
        ops_w = round(w.operational_weight * norm_factor, 4)
        cap_act_w = round(w.capacity_activation_weight * norm_factor, 4)

        overall = (
            rec_w * recruitment_risk
            + comp_w * compliance_risk
            + dq_w * data_quality_risk
            + exp_w * experience_risk
            + ops_w * operational_risk
            + cap_act_w * cap_act_combined
        )
        overall_score = round(max(0.0, min(100.0, overall)), 1)

        # Risk Level Classification
        if overall_score >= 65.0 or compliance_risk >= 75.0 or dev_analysis["critical_count"] >= 2:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 48.0 or compliance_risk >= 55.0 or dev_analysis["critical_count"] == 1:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 28.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Identify Specific Risk Factors
        risk_factors = []
        if recruitment_risk >= 50.0:
            risk_factors.append(f"Elevated recruitment risk ({recruitment_risk}/100): slow velocity or high screen failures.")
        if compliance_risk >= 45.0:
            risk_factors.append(f"Protocol compliance vulnerability ({compliance_risk}/100): documented deviation frequency.")
        if data_quality_risk >= 50.0:
            risk_factors.append(f"Data quality concern ({data_quality_risk}/100): query rate {site.data_query_rate} queries/CRF.")
        if activation_risk >= 60.0:
            risk_factors.append(f"Lengthy activation timeline ({site.activation_time_days} days).")
        if capacity_risk >= 50.0:
            risk_factors.append(f"Constrained coordinator staffing ({site.staff_capacity} staff).")
        if dev_analysis["critical_count"] > 0:
            risk_factors.append(f"{dev_analysis['critical_count']} CRITICAL protocol deviation(s) on record.")

        requires_review = (risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]) or (compliance_risk >= 60.0)

        # Mathematical breakdown
        math_breakdown = {
            "recruitment_term": round(rec_w * recruitment_risk, 2),
            "compliance_term": round(comp_w * compliance_risk, 2),
            "data_quality_term": round(dq_w * data_quality_risk, 2),
            "experience_term": round(exp_w * experience_risk, 2),
            "operational_term": round(ops_w * operational_risk, 2),
            "capacity_activation_term": round(cap_act_w * cap_act_combined, 2),
            "total_weighted_sum": overall_score,
            "formula": (
                f"{rec_w}*Recruit({recruitment_risk}) + "
                f"{comp_w}*Compl({compliance_risk}) + "
                f"{dq_w}*DataQ({data_quality_risk}) + "
                f"{exp_w}*Exp({experience_risk}) + "
                f"{ops_w}*Ops({operational_risk}) + "
                f"{cap_act_w}*CapAct({round(cap_act_combined, 1)})"
            ),
        }

        return SiteRisk(
            site_id=site.site_id,
            site_name=site.site_name,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            recruitment_risk=recruitment_risk,
            operational_risk=operational_risk,
            compliance_risk=compliance_risk,
            data_quality_risk=data_quality_risk,
            capacity_risk=capacity_risk,
            activation_risk=activation_risk,
            risk_factors=risk_factors,
            mathematical_breakdown=math_breakdown,
            requires_human_review=requires_review,
        )

    def assess_all_sites(
        self, sites: List[TrialSite], deviations: List[ProtocolDeviation] = None
    ) -> List[SiteRisk]:
        """Assesses risk for all candidate sites."""
        return [self.assess_site_risk(s, deviations) for s in sites]


site_risk_engine = SiteRiskEngine()
