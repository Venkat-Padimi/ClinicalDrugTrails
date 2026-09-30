"""Audit test verifying exact mathematical accuracy of site ranking calculations."""

import pytest
from src.domain.models import TrialSite
from src.engines.site_ranking_engine import SiteRankingEngine
from src.engines.site_intelligence_engine import SiteIntelligenceEngine
from src.engines.site_risk_engine import SiteRiskEngine
from src.config import SiteRankingWeights

def test_site_ranking_exact_mathematical_breakdown():
    weights = SiteRankingWeights(
        recruitment_score_weight=0.30,
        operational_score_weight=0.20,
        experience_score_weight=0.20,
        data_quality_weight=0.15,
        compliance_score_weight=0.15,
    )
    intel_engine = SiteIntelligenceEngine()
    risk_engine = SiteRiskEngine()
    ranking_engine = SiteRankingEngine(weights=weights, intelligence_engine=intel_engine, risk_engine=risk_engine)

    site = TrialSite(
        site_id="AUDIT-SITE-101",
        site_name="Academic Cancer Institute",
        city="Chicago",
        state="IL",
        country="USA",
        therapeutic_area_experience_years=15.0,
        investigator_experience_years=18.0,
        historical_trials_completed=30,
        historical_enrollment=450,
        average_monthly_enrollment=5.0,
        screen_failure_rate=0.10,
        dropout_rate=0.05,
        protocol_deviation_rate=0.2,
        data_query_rate=0.5,
        activation_time_days=45,
        recruitment_start_delay_days=5,
        staff_capacity=10,
        patient_pool_estimate=500,
    )

    perf = intel_engine.evaluate_site(site)
    risk = risk_engine.assess_site_risk(site, [])
    rankings = ranking_engine.rank_sites([site], [perf], [risk])

    assert len(rankings) == 1
    r = rankings[0]

    # Verify Base Score calculation
    expected_base = (
        (0.30 * perf.enrollment_velocity_score)
        + (0.20 * perf.operational_efficiency_score)
        + (0.20 * perf.experience_score)
        + (0.15 * perf.data_quality_score)
        + (0.15 * perf.compliance_score)
    )

    # Verify Risk penalty calculation
    expected_penalty = (risk.overall_risk_score / 100.0) * 25.0
    expected_priority = max(0.0, min(100.0, round(expected_base - expected_penalty, 1)))

    assert r.priority_score == expected_priority

    # Verify Confidence calculation
    trials_factor = min(1.0, site.historical_trials_completed / 30.0)
    dq_factor = perf.data_quality_score / 100.0
    expected_confidence = round(min(0.98, max(0.60, 0.70 + (0.15 * trials_factor) + (0.13 * dq_factor))), 2)

    assert r.confidence == expected_confidence

    # Verify Rationale embeds identical numbers
    assert str(expected_priority) in r.rationale
    assert str(site.average_monthly_enrollment) in r.rationale
    assert "synthetic" in r.rationale.lower()
