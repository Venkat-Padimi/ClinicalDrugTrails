"""Unit tests for ProtocolDeviationEngine."""

import pytest
from src.domain.models import ProtocolDeviation, DeviationSeverity, DeviationCategory, TrialSite, RiskLevel
from src.engines.protocol_deviation_engine import ProtocolDeviationEngine

def test_site_deviations_clean_site():
    engine = ProtocolDeviationEngine()
    analysis = engine.analyze_site_deviations("SITE-CLEAN", "Clean Clinic", [])
    assert analysis["total_deviations"] == 0
    assert analysis["deviation_risk_score"] == 0.0
    assert analysis["risk_level"] == RiskLevel.LOW
    assert "FACT" in analysis["facts"][0]
    assert "INTERPRETATION" in analysis["interpretations"][0]

def test_site_deviations_critical_site():
    engine = ProtocolDeviationEngine()
    devs = [
        ProtocolDeviation(
            deviation_id="D1",
            site_id="SITE-RISK",
            trial_id="T1",
            category=DeviationCategory.INVESTIGATIONAL_PRODUCT,
            severity=DeviationSeverity.CRITICAL,
            occurrence_date="2026-01-01",
            resolved=False,
            recurrence=True,
            description="Excursion",
        ),
        ProtocolDeviation(
            deviation_id="D2",
            site_id="SITE-RISK",
            trial_id="T1",
            category=DeviationCategory.INCLUSION_VIOLATION,
            severity=DeviationSeverity.CRITICAL,
            occurrence_date="2026-02-01",
            resolved=False,
            recurrence=True,
            description="Enrolled wrong pt",
        ),
    ]

    analysis = engine.analyze_site_deviations("SITE-RISK", "High Risk Center", devs)
    assert analysis["total_deviations"] == 2
    assert analysis["critical_count"] == 2
    assert analysis["risk_level"] == RiskLevel.CRITICAL
    assert analysis["deviation_risk_score"] >= 70.0
    assert any("CRITICAL" in interp for interp in analysis["interpretations"])
    assert any("FACT" in f for f in analysis["facts"])

def test_deviation_summary_outliers():
    engine = ProtocolDeviationEngine()
    sites = [
        TrialSite(
            site_id=f"SITE-{i}",
            site_name=f"Site {i}",
            city="City",
            state="ST",
            country="USA",
            therapeutic_area_experience_years=5.0,
            investigator_experience_years=5.0,
            historical_trials_completed=5,
            historical_enrollment=50,
            average_monthly_enrollment=1.0,
            screen_failure_rate=0.2,
            dropout_rate=0.1,
            protocol_deviation_rate=0.5,
            data_query_rate=1.0,
            activation_time_days=60,
            recruitment_start_delay_days=10,
            staff_capacity=4,
            patient_pool_estimate=100,
        )
        for i in range(1, 6)
    ]
    # SITE-1 has 10 deviations, others have 0-1
    devs = []
    for j in range(10):
        devs.append(
            ProtocolDeviation(
                deviation_id=f"D-S1-{j}",
                site_id="SITE-1",
                trial_id="T1",
                category=DeviationCategory.VISIT_WINDOW,
                severity=DeviationSeverity.LOW,
                occurrence_date="2026-01-01",
                resolved=True,
                recurrence=False,
                description="Window",
            )
        )
    devs.append(
        ProtocolDeviation(
            deviation_id="D-S2-1",
            site_id="SITE-2",
            trial_id="T1",
            category=DeviationCategory.DOCUMENTATION,
            severity=DeviationSeverity.LOW,
            occurrence_date="2026-01-01",
            resolved=True,
            recurrence=False,
            description="Doc",
        )
    )

    summary = engine.summarize_all(devs, sites)
    assert summary.total_deviations == 11
    assert "SITE-1" in summary.site_deviation_counts
    assert any("outlier" in interp.lower() for interp in summary.interpretations)
