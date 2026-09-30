"""Unit tests for SiteRankingEngine."""

import pytest
from src.domain.models import TrialSite
from src.engines.site_ranking_engine import SiteRankingEngine

def test_site_ranking_engine_ordering():
    engine = SiteRankingEngine()
    
    elite = TrialSite(
        site_id="SITE-1",
        site_name="Elite Academic Center",
        city="Boston",
        state="MA",
        country="USA",
        therapeutic_area_experience_years=15.0,
        investigator_experience_years=18.0,
        historical_trials_completed=40,
        historical_enrollment=500,
        average_monthly_enrollment=5.2,
        screen_failure_rate=0.12,
        dropout_rate=0.04,
        protocol_deviation_rate=0.2,
        data_query_rate=0.6,
        activation_time_days=48,
        recruitment_start_delay_days=5,
        staff_capacity=10,
        patient_pool_estimate=600,
    )

    middle = TrialSite(
        site_id="SITE-2",
        site_name="Average Community Hospital",
        city="Columbus",
        state="OH",
        country="USA",
        therapeutic_area_experience_years=9.0,
        investigator_experience_years=10.0,
        historical_trials_completed=18,
        historical_enrollment=220,
        average_monthly_enrollment=3.0,
        screen_failure_rate=0.22,
        dropout_rate=0.09,
        protocol_deviation_rate=0.7,
        data_query_rate=1.4,
        activation_time_days=75,
        recruitment_start_delay_days=15,
        staff_capacity=5,
        patient_pool_estimate=250,
    )

    poor = TrialSite(
        site_id="SITE-3",
        site_name="Lagging Clinic",
        city="Smalltown",
        state="WY",
        country="USA",
        therapeutic_area_experience_years=3.0,
        investigator_experience_years=4.0,
        historical_trials_completed=4,
        historical_enrollment=35,
        average_monthly_enrollment=0.9,
        screen_failure_rate=0.42,
        dropout_rate=0.20,
        protocol_deviation_rate=2.6,
        data_query_rate=3.2,
        activation_time_days=125,
        recruitment_start_delay_days=35,
        staff_capacity=2,
        patient_pool_estimate=75,
    )

    rankings = engine.rank_sites([middle, poor, elite])
    assert len(rankings) == 3
    assert rankings[0].site_id == "SITE-1"
    assert rankings[0].rank == 1
    assert rankings[1].site_id == "SITE-2"
    assert rankings[1].rank == 2
    assert rankings[2].site_id == "SITE-3"
    assert rankings[2].rank == 3

    assert rankings[0].priority_score > rankings[1].priority_score > rankings[2].priority_score
    assert len(rankings[0].strengths) >= 2
    assert len(rankings[2].weaknesses) >= 2
    assert "synthetic" in rankings[0].rationale.lower()
    assert rankings[2].requires_review is True
