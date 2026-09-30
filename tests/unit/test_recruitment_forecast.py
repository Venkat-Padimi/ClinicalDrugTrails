"""Unit tests for RecruitmentForecastEngine."""

import pytest
from src.domain.models import Trial, TrialSite, RiskLevel
from src.engines.recruitment_forecast_engine import RecruitmentForecastEngine

def test_recruitment_forecast_sufficient_capacity():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TEST-TRIAL-01",
        trial_name="Test Trial",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=100,
        enrollment_deadline="2028-12-31",  # Plenty of time
    )
    sites = [
        TrialSite(
            site_id=f"SITE-{i}",
            site_name=f"Site {i}",
            city="City",
            state="ST",
            country="USA",
            therapeutic_area_experience_years=10.0,
            investigator_experience_years=10.0,
            historical_trials_completed=20,
            historical_enrollment=200,
            average_monthly_enrollment=3.0,
            screen_failure_rate=0.15,
            dropout_rate=0.08,
            protocol_deviation_rate=0.5,
            data_query_rate=1.0,
            activation_time_days=60,
            recruitment_start_delay_days=10,
            staff_capacity=6,
            patient_pool_estimate=300,
        )
        for i in range(5)
    ]

    forecast = engine.forecast_enrollment(trial, sites, eligible_patient_pool=400)
    assert forecast.expected_monthly_enrollment > 10.0
    assert forecast.p10_time_months < forecast.p50_time_months < forecast.p90_time_months
    assert forecast.enrollment_probability >= 0.80
    assert forecast.recruitment_shortfall == 0
    assert forecast.recruitment_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    assert forecast.expected_screen_failures > 0
    assert forecast.expected_dropout_impact > 0

def test_recruitment_forecast_insufficient_sites():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TEST-TRIAL-02",
        trial_name="Test Trial 2",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=300,
        enrollment_deadline="2026-11-01",  # Imminent deadline
    )
    sites = [
        TrialSite(
            site_id="SITE-SINGLE",
            site_name="Slow Site",
            city="City",
            state="ST",
            country="USA",
            therapeutic_area_experience_years=3.0,
            investigator_experience_years=4.0,
            historical_trials_completed=3,
            historical_enrollment=20,
            average_monthly_enrollment=0.8,
            screen_failure_rate=0.35,
            dropout_rate=0.18,
            protocol_deviation_rate=1.5,
            data_query_rate=2.0,
            activation_time_days=90,
            recruitment_start_delay_days=30,
            staff_capacity=2,
            patient_pool_estimate=50,
        )
    ]

    forecast = engine.forecast_enrollment(trial, sites, eligible_patient_pool=50)
    assert forecast.recruitment_shortfall > 0
    assert forecast.recruitment_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert forecast.enrollment_probability < 0.60
