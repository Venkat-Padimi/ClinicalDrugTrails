"""Recruitment Forecast Engine.

Calculates transparent, deterministic enrollment timelines, multi-scenario projections
(P10 optimistic, P50 expected, P90 conservative), screen failure impact, dropout friction,
and recruitment shortfall risk.
All projections are synthetic estimates.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.domain.models import (
    Trial,
    TrialSite,
    RecruitmentForecast,
    RiskLevel,
)


class RecruitmentForecastEngine:
    """Deterministic forecasting engine for clinical trial enrollment."""

    def calculate_months_to_deadline(self, deadline_str: str) -> float:
        """Calculates months remaining from current date to trial deadline."""
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            now = datetime.now()
            days = (deadline - now).days
            return max(1.0, round(days / 30.4375, 1))
        except Exception:
            return 18.0  # Safe default assumption: 18 months

    def forecast_enrollment(
        self,
        trial: Trial,
        sites: List[TrialSite],
        eligible_patient_pool: int,
        conversion_rate: float = 0.65,
    ) -> RecruitmentForecast:
        """Generates comprehensive recruitment projection with uncertainty bounds."""
        target = trial.target_enrollment
        if not sites:
            # Fallback if no sites selected
            return RecruitmentForecast(
                trial_id=trial.trial_id,
                target_enrollment=target,
                eligible_patient_pool=eligible_patient_pool,
                expected_monthly_enrollment=0.0,
                time_to_target_months=999.0,
                p10_time_months=999.0,
                p50_time_months=999.0,
                p90_time_months=999.0,
                enrollment_probability=0.0,
                recruitment_shortfall=target,
                recruitment_risk_level=RiskLevel.CRITICAL,
                expected_screen_failures=0,
                expected_dropout_impact=0,
                assumptions={"error": "No candidate sites provided."},
            )

        # 1. Base monthly capacity across sites
        raw_monthly_rate = sum(s.average_monthly_enrollment for s in sites)

        # 2. Weighted screen failure and dropout rates
        avg_sf_rate = sum(s.screen_failure_rate for s in sites) / len(sites)
        avg_do_rate = sum(s.dropout_rate for s in sites) / len(sites)

        # 3. Expected screen failures and dropout impact
        expected_screen_failures = int(round(target * (avg_sf_rate / max(0.01, 1.0 - avg_sf_rate))))
        expected_dropout_impact = int(round(target * avg_do_rate))
        
        # Effective enrollment needed to ensure 'target' completed evaluable patients
        effective_target = int(round(target / max(0.01, 1.0 - avg_do_rate)))

        # 4. Realistic monthly rate adjusted for screen failure friction
        # Higher screen failure consumes site staff capacity
        operational_efficiency_factor = max(0.5, 1.0 - (0.5 * avg_sf_rate))
        expected_monthly = round(max(0.2, raw_monthly_rate * operational_efficiency_factor), 2)

        # 5. Expected time to target (months)
        p50_time = round(effective_target / expected_monthly, 1)

        # 6. Uncertainty bounds
        # P10: Optimistic scenario (25% faster recruitment)
        p10_time = round(max(1.0, p50_time * 0.75), 1)
        # P90: Conservative scenario (35% slower due to holidays, startup delay, protocol friction)
        p90_time = round(p50_time * 1.35, 1)

        # 7. Deadline evaluation & enrollment probability
        months_available = self.calculate_months_to_deadline(trial.enrollment_deadline)

        if months_available >= p90_time:
            enrollment_probability = 0.94
            risk_level = RiskLevel.LOW
            shortfall = 0
        elif months_available >= p50_time:
            # Probability between 0.70 and 0.90
            ratio = (months_available - p50_time) / max(0.1, (p90_time - p50_time))
            enrollment_probability = round(0.70 + (0.24 * (1.0 - ratio)), 2)
            risk_level = RiskLevel.MEDIUM
            shortfall = 0
        elif months_available >= p10_time:
            ratio = (months_available - p10_time) / max(0.1, (p50_time - p10_time))
            enrollment_probability = round(0.35 + (0.35 * ratio), 2)
            risk_level = RiskLevel.HIGH
            projected_enrolled = int(months_available * expected_monthly)
            shortfall = max(0, effective_target - projected_enrolled)
        else:
            enrollment_probability = max(0.05, round(0.30 * (months_available / max(0.1, p10_time)), 2))
            risk_level = RiskLevel.CRITICAL
            projected_enrolled = int(months_available * expected_monthly)
            shortfall = max(0, effective_target - projected_enrolled)

        # 8. Check patient pool sufficiency
        # Recruitable pool estimate = eligible_patient_pool * conversion_rate
        estimated_recruitable = int(eligible_patient_pool * conversion_rate)
        if estimated_recruitable < effective_target:
            pool_deficit = effective_target - estimated_recruitable
            shortfall = max(shortfall, pool_deficit)
            if risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                risk_level = RiskLevel.HIGH

        assumptions = {
            "num_sites": len(sites),
            "raw_site_monthly_capacity": round(raw_monthly_rate, 2),
            "average_screen_failure_rate": round(avg_sf_rate, 3),
            "average_dropout_rate": round(avg_do_rate, 3),
            "effective_target_with_dropout": effective_target,
            "patient_conversion_rate": conversion_rate,
            "estimated_recruitable_from_pool": estimated_recruitable,
            "months_to_deadline": months_available,
            "formula_note": "Time = Effective Target / (Site Velocity * Efficiency Factor)",
        }

        return RecruitmentForecast(
            trial_id=trial.trial_id,
            target_enrollment=target,
            eligible_patient_pool=eligible_patient_pool,
            expected_monthly_enrollment=expected_monthly,
            time_to_target_months=p50_time,
            p10_time_months=p10_time,
            p50_time_months=p50_time,
            p90_time_months=p90_time,
            enrollment_probability=enrollment_probability,
            recruitment_shortfall=shortfall,
            recruitment_risk_level=risk_level,
            expected_screen_failures=expected_screen_failures,
            expected_dropout_impact=expected_dropout_impact,
            assumptions=assumptions,
        )


recruitment_forecast_engine = RecruitmentForecastEngine()
