"""Unit tests for SiteRiskEngine."""

import pytest
from src.domain.models import TrialSite, RiskLevel
from src.config import RiskScoringWeights
from src.engines.site_risk_engine import SiteRiskEngine

def test_site_risk_calculation():
    engine = SiteRiskEngine()
    
    # Safe site
    safe_site = TrialSite(
        site_id="SITE-SAFE",
        site_name="Safe Clinical Center",
        city="Chicago",
        state="IL",
        country="USA",
        therapeutic_area_experience_years=15.0,
        investigator_experience_years=18.0,
        historical_trials_completed=35,
        historical_enrollment=500,
        average_monthly_enrollment=5.0,
        screen_failure_rate=0.10,
        dropout_rate=0.04,
        protocol_deviation_rate=0.2,
        data_query_rate=0.6,
        activation_time_days=45,
        recruitment_start_delay_days=5,
        staff_capacity=10,
        patient_pool_estimate=600,
    )

    risk_safe = engine.assess_site_risk(safe_site, [])
    assert risk_safe.overall_risk_score < 30.0
    assert risk_safe.risk_level == RiskLevel.LOW
    assert risk_safe.requires_human_review is False
    assert "formula" in risk_safe.mathematical_breakdown

    # High risk site
    risky_site = TrialSite(
        site_id="SITE-RISK",
        site_name="Struggling Clinic",
        city="Detroit",
        state="MI",
        country="USA",
        therapeutic_area_experience_years=3.0,
        investigator_experience_years=3.0,
        historical_trials_completed=4,
        historical_enrollment=30,
        average_monthly_enrollment=0.8,
        screen_failure_rate=0.45,
        dropout_rate=0.22,
        protocol_deviation_rate=2.8,
        data_query_rate=3.5,
        activation_time_days=130,
        recruitment_start_delay_days=40,
        staff_capacity=2,
        patient_pool_estimate=70,
    )

    risk_high = engine.assess_site_risk(risky_site, [])
    assert risk_high.overall_risk_score > 60.0
    assert risk_high.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert risk_high.requires_human_review is True
    assert len(risk_high.risk_factors) >= 3

def test_configurable_risk_weights():
    # Emphasize recruitment over compliance
    custom_weights = RiskScoringWeights(
        recruitment_weight=0.50,
        compliance_weight=0.10,
        data_quality_weight=0.10,
        investigator_experience_weight=0.10,
        operational_weight=0.10,
        capacity_activation_weight=0.10
    )
    assert custom_weights.validate() is True

    engine = SiteRiskEngine(weights=custom_weights)
    site = TrialSite(
        site_id="SITE-FAST-BUT-SLOPPY",
        site_name="Fast Site",
        city="Miami",
        state="FL",
        country="USA",
        therapeutic_area_experience_years=10.0,
        investigator_experience_years=10.0,
        historical_trials_completed=20,
        historical_enrollment=300,
        average_monthly_enrollment=5.0,  # Fast!
        screen_failure_rate=0.12,
        dropout_rate=0.08,
        protocol_deviation_rate=2.5,   # High deviations!
        data_query_rate=2.5,
        activation_time_days=60,
        recruitment_start_delay_days=10,
        staff_capacity=6,
        patient_pool_estimate=300,
    )

    risk = engine.assess_site_risk(site, [])
    # Since recruitment is 50% weighted and recruitment risk is low, overall risk is buffered
    assert risk.recruitment_risk < 25.0
    assert risk.mathematical_breakdown["recruitment_term"] == pytest.approx(0.50 * risk.recruitment_risk, 0.05)
