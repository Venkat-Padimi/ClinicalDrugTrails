"""Protocol Deviation Monitoring Engine.

Detects high-frequency, recurring, unresolved, and severe clinical deviations.
Explicitly separates verifiable clinical FACTS from analytical risk INTERPRETATIONS.
Calculates deterministic compliance and deviation risk indicators.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
import numpy as np

from src.domain.models import (
    ProtocolDeviation,
    DeviationSeverity,
    DeviationCategory,
    ProtocolDeviationSummary,
    TrialSite,
    RiskLevel,
)


class ProtocolDeviationEngine:
    """Deterministic monitoring engine for protocol deviations."""

    def analyze_site_deviations(
        self, site_id: str, site_name: str, deviations: List[ProtocolDeviation]
    ) -> Dict[str, Any]:
        """Analyzes deviations for a specific site with factual and interpretative separation."""
        site_devs = [d for d in deviations if d.site_id == site_id]
        total = len(site_devs)

        if total == 0:
            facts = [f"FACT: Site '{site_name}' ({site_id}) has 0 recorded synthetic protocol deviations."]
            interpretations = [f"INTERPRETATION: Site displays clean compliance record based on current synthetic audit logs."]
            return {
                "site_id": site_id,
                "site_name": site_name,
                "total_deviations": 0,
                "unresolved_count": 0,
                "recurrence_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "deviation_risk_score": 0.0,
                "risk_level": RiskLevel.LOW,
                "facts": facts,
                "interpretations": interpretations,
            }

        unresolved = sum(1 for d in site_devs if not d.resolved)
        recurrence = sum(1 for d in site_devs if d.recurrence)
        crit = sum(1 for d in site_devs if d.severity == DeviationSeverity.CRITICAL)
        high = sum(1 for d in site_devs if d.severity == DeviationSeverity.HIGH)
        med = sum(1 for d in site_devs if d.severity == DeviationSeverity.MEDIUM)
        low = sum(1 for d in site_devs if d.severity == DeviationSeverity.LOW)

        # Deterministic Risk Scoring (0 = pristine, 100 = critical non-compliance)
        raw_points = (
            (5.0 * low)
            + (15.0 * med)
            + (30.0 * high)
            + (50.0 * crit)
            + (15.0 * unresolved)
            + (20.0 * recurrence)
        )
        # Normalize: 120 points represents critical risk threshold
        risk_score = min(100.0, round((raw_points / 120.0) * 100.0, 1))

        if risk_score >= 70.0 or crit >= 2:
            risk_lvl = RiskLevel.CRITICAL
        elif risk_score >= 45.0 or (crit == 1 or high >= 2):
            risk_lvl = RiskLevel.HIGH
        elif risk_score >= 25.0:
            risk_lvl = RiskLevel.MEDIUM
        else:
            risk_lvl = RiskLevel.LOW

        # Facts: strictly empirical counts and statuses
        facts = [
            f"FACT: Site recorded {total} total synthetic protocol deviations ({crit} Critical, {high} High, {med} Medium, {low} Low).",
            f"FACT: {unresolved} deviation(s) remain unresolved; {recurrence} event(s) exhibit documented recurrence.",
        ]

        # Interpretations: analytical deductions and operational warnings
        interpretations = []
        if crit > 0:
            interpretations.append(
                f"INTERPRETATION: Presence of {crit} CRITICAL deviation(s) (e.g. drug excursion or eligibility violation) indicates severe procedural vulnerability requiring immediate CAPA."
            )
        if recurrence > 0:
            interpretations.append(
                f"INTERPRETATION: Recurrence rate ({recurrence}/{total}) indicates systemic procedural breakdown rather than isolated human error."
            )
        if unresolved > 2:
            interpretations.append(
                f"INTERPRETATION: High unresolved backlog ({unresolved} open deviations) reflects site coordinator capacity constraints or monitoring delay."
            )
        if not interpretations:
            interpretations.append(
                "INTERPRETATION: Minor deviation profile is within acceptable operational tolerance for complex Phase III trials."
            )

        return {
            "site_id": site_id,
            "site_name": site_name,
            "total_deviations": total,
            "unresolved_count": unresolved,
            "recurrence_count": recurrence,
            "critical_count": crit,
            "high_count": high,
            "medium_count": med,
            "low_count": low,
            "deviation_risk_score": risk_score,
            "risk_level": risk_lvl,
            "facts": facts,
            "interpretations": interpretations,
        }

    def summarize_all(
        self, deviations: List[ProtocolDeviation], sites: List[TrialSite]
    ) -> ProtocolDeviationSummary:
        """Produces aggregate protocol deviation summary with anomaly detection."""
        sev_counts: Counter = Counter()
        cat_counts: Counter = Counter()
        site_counts: Dict[str, int] = {s.site_id: 0 for s in sites}
        unresolved_total = 0
        recurrence_total = 0

        for d in deviations:
            sev_counts[d.severity] += 1
            cat_counts[d.category] += 1
            site_counts[d.site_id] = site_counts.get(d.site_id, 0) + 1
            if not d.resolved:
                unresolved_total += 1
            if d.recurrence:
                recurrence_total += 1

        total = len(deviations)
        site_map = {s.site_id: s.site_name for s in sites}

        # Anomaly Detection: sites with deviations > mean + 1.5 * std
        counts_arr = np.array(list(site_counts.values())) if site_counts else np.array([0])
        mean_devs = float(np.mean(counts_arr)) if len(counts_arr) > 0 else 0.0
        std_devs = float(np.std(counts_arr)) if len(counts_arr) > 0 else 0.0
        anomaly_thresh = mean_devs + (1.5 * std_devs)

        outlier_sites = [sid for sid, c in site_counts.items() if c > anomaly_thresh]

        facts = [
            f"FACT: Analyzed {total} synthetic protocol deviations across {len(sites)} participating sites.",
            f"FACT: Overall severity breakdown: {dict(sev_counts)}.",
            f"FACT: {unresolved_total} of {total} deviations are currently open/unresolved ({round(unresolved_total/max(1, total)*100, 1)}%).",
        ]

        interpretations = []
        if outlier_sites:
            outlier_names = [f"{site_map.get(s, s)} ({site_counts[s]} deviations)" for s in outlier_sites]
            interpretations.append(
                f"INTERPRETATION: Statistical outlier sites detected above threshold {round(anomaly_thresh, 1)}: {', '.join(outlier_names)}. "
                "Targeted GCP audit recommended."
            )
        if sev_counts[DeviationSeverity.CRITICAL] > 0:
            interpretations.append(
                f"INTERPRETATION: Total of {sev_counts[DeviationSeverity.CRITICAL]} critical deviations require protocol-wide safety review."
            )

        return ProtocolDeviationSummary(
            total_deviations=total,
            severity_breakdown=dict(sev_counts),
            category_breakdown=dict(cat_counts),
            unresolved_count=unresolved_total,
            recurrence_count=recurrence_total,
            site_deviation_counts=dict(site_counts),
            facts=facts,
            interpretations=interpretations,
        )


protocol_deviation_engine = ProtocolDeviationEngine()
