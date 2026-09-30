"""Audit tests for Protocol Deviation Engine."""

import pytest
from src.domain.models import ProtocolDeviation, DeviationSeverity, DeviationCategory, RiskLevel, TrialSite
from src.engines.protocol_deviation_engine import ProtocolDeviationEngine

def test_protocol_deviation_audit_profiles():
    engine = ProtocolDeviationEngine()

    # 1. Zero Deviations
    res_zero = engine.analyze_site_deviations("SITE-0", "Clean Site", [])
    assert res_zero["deviation_risk_score"] == 0.0
    assert res_zero["risk_level"] == RiskLevel.LOW
    assert len(res_zero["facts"]) > 0

    # 2. Minor Low Volume
    minor_dev = ProtocolDeviation(
        deviation_id="D-MIN",
        site_id="SITE-1",
        trial_id="T1",
        category=DeviationCategory.VISIT_WINDOW,
        severity=DeviationSeverity.LOW,
        occurrence_date="2026-03-01",
        resolved=True,
        recurrence=False,
        description="Visit rescheduled 1 day late.",
    )
    res_minor = engine.analyze_site_deviations("SITE-1", "Minor Site", [minor_dev])
    assert res_minor["deviation_risk_score"] < 25.0
    assert res_minor["risk_level"] == RiskLevel.LOW

    # 3. Recurring Deviations
    rec_devs = [
        ProtocolDeviation(
            deviation_id=f"D-REC-{i}",
            site_id="SITE-REC",
            trial_id="T1",
            category=DeviationCategory.INFORMED_CONSENT,
            severity=DeviationSeverity.MEDIUM,
            occurrence_date=f"2026-0{i+1}-01",
            resolved=True,
            recurrence=True,  # All recurring
            description="Re-consent amendment delay.",
        )
        for i in range(3)
    ]
    res_rec = engine.analyze_site_deviations("SITE-REC", "Recurring Site", rec_devs)
    assert res_rec["recurrence_count"] == 3
    assert any("systemic" in interp.lower() for interp in res_rec["interpretations"])

    # 4. Severe Critical Deviation
    crit_dev = ProtocolDeviation(
        deviation_id="D-CRIT",
        site_id="SITE-CRIT",
        trial_id="T1",
        category=DeviationCategory.INCLUSION_VIOLATION,
        severity=DeviationSeverity.CRITICAL,
        occurrence_date="2026-04-01",
        resolved=False,
        recurrence=False,
        description="Patient enrolled below protocol renal threshold.",
    )
    res_crit = engine.analyze_site_deviations("SITE-CRIT", "Critical Site", [crit_dev])
    assert res_crit["critical_count"] == 1
    assert res_crit["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert any("CRITICAL" in interp for interp in res_crit["interpretations"])

    # 5. High Unresolved Backlog
    backlog_devs = [
        ProtocolDeviation(
            deviation_id=f"D-OPEN-{i}",
            site_id="SITE-BACKLOG",
            trial_id="T1",
            category=DeviationCategory.LAB_PROTOCOL,
            severity=DeviationSeverity.LOW,
            occurrence_date=f"2026-0{i+1}-01",
            resolved=False,  # All unresolved
            recurrence=False,
            description="Missing local lab waiver.",
        )
        for i in range(5)
    ]
    res_backlog = engine.analyze_site_deviations("SITE-BACKLOG", "Backlog Site", backlog_devs)
    assert res_backlog["unresolved_count"] == 5
    assert any("unresolved backlog" in interp.lower() for interp in res_backlog["interpretations"])
