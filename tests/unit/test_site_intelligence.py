"""Unit tests for SiteIntelligenceEngine."""

import pytest
from src.domain.models import TrialSite
from src.engines.site_intelligence_engine import SiteIntelligenceEngine

def test_site_intelligence_evaluation():
    engine = SiteIntelligenceEngine()
    
    # High-performing site
    elite_site = TrialSite(
        site_id="SITE-TOP",
        site_name="Top Tier Cancer Center",
        city="Boston",
        state="MA",
        country="USA",
        therapeutic_area_experience_years=15.0,
        investigator_experience_years=18.0,
        historical_trials_completed=40,
        historical_enrollment=500,
        average_monthly_enrollment=5.0,
        screen_failure_rate=0.12,
        dropout_rate=0.05,
        protocol_deviation_rate=0.25,
        data_query_rate=0.6,
        activation_time_days=45,
        recruitment_start_delay_days=5,
        staff_capacity=10,
        patient_pool_estimate=600,
    )
    
    perf_elite = engine.evaluate_site(elite_site)
    assert perf_elite.site_id == "SITE-TOP"
    assert perf_elite.enrollment_velocity_score == 100.0
    assert perf_elite.experience_score == 100.0
    assert perf_elite.compliance_score >= 90.0
    assert perf_elite.composite_performance_score >= 90.0

    # Low-performing site
    low_site = TrialSite(
        site_id="SITE-LOW",
        site_name="Underperforming Clinic",
        city="Rural",
        state="NV",
        country="USA",
        therapeutic_area_experience_years=3.0,
        investigator_experience_years=4.0,
        historical_trials_completed=5,
        historical_enrollment=50,
        average_monthly_enrollment=1.0,
        screen_failure_rate=0.40,
        dropout_rate=0.20,
        protocol_deviation_rate=2.5,
        data_query_rate=3.0,
        activation_time_days=120,
        recruitment_start_delay_days=35,
        staff_capacity=2,
        patient_pool_estimate=80,
    )

    perf_low = engine.evaluate_site(low_site)
    assert perf_low.enrollment_velocity_score < 30.0
    assert perf_low.composite_performance_score < 45.0
    assert perf_elite.composite_performance_score > perf_low.composite_performance_score
