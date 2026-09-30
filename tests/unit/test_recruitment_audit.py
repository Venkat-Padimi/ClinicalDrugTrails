"""Audit tests for Recruitment Forecast Engine edge cases."""

import pytest
from src.domain.models import Trial, TrialSite, RiskLevel
from src.engines.recruitment_forecast_engine import RecruitmentForecastEngine


def test_recruitment_empty_sites():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TRIAL-EMPTY-SITES",
        trial_name="Trial Empty",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=100,
        enrollment_deadline="2027-12-31",
    )

    forecast = engine.forecast_enrollment(trial, [], eligible_patient_pool=100)
    assert forecast.expected_monthly_enrollment == 0.0
    assert forecast.recruitment_risk_level == RiskLevel.CRITICAL
    assert forecast.recruitment_shortfall == 100
    assert "error" in forecast.assumptions


def test_recruitment_extreme_screen_failure_and_dropout():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TRIAL-EXTREME-RATES",
        trial_name="Trial Extreme",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=50,
        enrollment_deadline="2028-12-31",
    )
    # Site with near 100% screen failure and near 100% dropout
    extreme_site = TrialSite(
        site_id="SITE-EXTREME",
        site_name="Extreme Clinic",
        city="City",
        state="ST",
        country="USA",
        therapeutic_area_experience_years=5.0,
        investigator_experience_years=5.0,
        historical_trials_completed=5,
        historical_enrollment=50,
        average_monthly_enrollment=2.0,
        screen_failure_rate=0.95,  # 95% fail!
        dropout_rate=0.90,         # 90% dropout!
        protocol_deviation_rate=1.0,
        data_query_rate=1.0,
        activation_time_days=60,
        recruitment_start_delay_days=10,
        staff_capacity=4,
        patient_pool_estimate=100,
    )

    # Should not raise ZeroDivisionError or NaN
    forecast = engine.forecast_enrollment(trial, [extreme_site], eligible_patient_pool=500)
    assert forecast.expected_monthly_enrollment > 0
    assert forecast.expected_screen_failures > 0
    assert forecast.expected_dropout_impact > 0
    assert forecast.p10_time_months <= forecast.p50_time_months <= forecast.p90_time_months


def test_recruitment_zero_eligible_pool():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TRIAL-ZERO-POOL",
        trial_name="Trial Zero Pool",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=100,
        enrollment_deadline="2027-12-31",
    )
    site = TrialSite(
        site_id="SITE-OK",
        site_name="OK Site",
        city="City",
        state="ST",
        country="USA",
        therapeutic_area_experience_years=10.0,
        investigator_experience_years=10.0,
        historical_trials_completed=10,
        historical_enrollment=100,
        average_monthly_enrollment=3.0,
        screen_failure_rate=0.20,
        dropout_rate=0.08,
        protocol_deviation_rate=0.5,
        data_query_rate=1.0,
        activation_time_days=60,
        recruitment_start_delay_days=10,
        staff_capacity=5,
        patient_pool_estimate=200,
    )

    forecast = engine.forecast_enrollment(trial, [site], eligible_patient_pool=0)
    assert forecast.recruitment_shortfall >= 100
    assert forecast.recruitment_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


def test_recruitment_past_deadline():
    engine = RecruitmentForecastEngine()
    trial = Trial(
        trial_id="TRIAL-PAST-DEADLINE",
        trial_name="Trial Expired",
        therapeutic_area="Oncology",
        phase="Phase III",
        target_population="Adults",
        target_enrollment=100,
        enrollment_deadline="2020-01-01",  # In the past!
    )
    site = TrialSite(
        site_id="SITE-OK",
        site_name="OK Site",
        city="City",
        state="ST",
        country="USA",
        therapeutic_area_experience_years=10.0,
        investigator_experience_years=10.0,
        historical_trials_completed=10,
        historical_enrollment=100,
        average_monthly_enrollment=3.0,
        screen_failure_rate=0.20,
        dropout_rate=0.08,
        protocol_deviation_rate=0.5,
        data_query_rate=1.0,
        activation_time_days=60,
        recruitment_start_delay_days=10,
        staff_capacity=5,
        patient_pool_estimate=200,
    )

    forecast = engine.forecast_enrollment(trial, [site], eligible_patient_pool=200)
    assert forecast.recruitment_risk_level == RiskLevel.CRITICAL
    assert forecast.enrollment_probability <= 0.35
