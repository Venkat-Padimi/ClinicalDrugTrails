"""Executive Reporting and Structured Export Engine.

Generates:
1. Executive Markdown Report (Clinical feasibility, site rankings, risk profiles)
2. Machine-readable JSON Export
3. Standard CSV exports for screening, sites, rankings, and deviations

All reports embed mandatory synthetic data disclaimers and complete audit summaries.
"""

from typing import Dict, Any, List
import json
import csv
import io
from datetime import datetime
from src.domain.models import TrialAnalysisResult
from src.config import config, DISCLAIMER_TEXT


class ExecutiveReportGenerator:
    """Generates executive summaries and machine-readable data exports."""

    def generate_markdown_report(self, result: TrialAnalysisResult) -> str:
        """Generates comprehensive executive trial and site selection report in Markdown."""
        trial = result.trial
        scr = result.screening_summary
        forecast = result.recruitment_forecast
        devs = result.deviation_summary
        top_site = result.site_rankings[0] if result.site_rankings else None

        md = []
        md.append(f"# Clinical Trial Site Selection & Feasibility Executive Report")
        md.append(f"**Trial:** {trial.trial_name} ({trial.trial_id})")
        md.append(f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**Protocol Version:** {trial.protocol_version} | **Phase:** {trial.phase} | **Therapeutic Area:** {trial.therapeutic_area}")
        md.append("\n---\n")

        # Mandatory Safety Disclaimer
        md.append(f"> **MANDATORY SAFETY DISCLAIMER:**\n> {DISCLAIMER_TEXT}\n")

        # 1. Executive Summary
        md.append("## 1. Executive Summary")
        md.append(
            f"This automated feasibility analysis evaluated **{scr.total_screened} synthetic patients** and "
            f"**{len(result.site_rankings)} candidate clinical trial sites** for protocol `{trial.trial_id}`. "
            f"The target enrollment is **{trial.target_enrollment} subjects** with a target deadline of `{trial.enrollment_deadline}`.\n"
        )
        if top_site:
            md.append(
                f"- **Top Prioritized Site:** **{top_site.site_name}** (`{top_site.site_id}`) — "
                f"Priority Score: **{top_site.priority_score}/100** (Confidence: {int(top_site.confidence*100)}%)."
            )
        md.append(f"- **Eligible Patient Pool:** {scr.eligible_count} subjects ({round(scr.eligibility_rate*100, 1)}% eligibility rate).")
        md.append(f"- **Expected Monthly Recruitment Rate:** {forecast.expected_monthly_enrollment} patients/month across active sites.")
        md.append(f"- **Projected Enrollment Timeline (P50):** {forecast.p50_time_months} months (P10: {forecast.p10_time_months} mo, P90: {forecast.p90_time_months} mo).")
        md.append(f"- **Recruitment Risk Level:** **{forecast.recruitment_risk_level.value}** (Probability of meeting deadline: {int(forecast.enrollment_probability*100)}%).")
        md.append(f"- **Protocol Deviations Monitored:** {devs.total_deviations} total events ({devs.unresolved_count} unresolved backlog).")

        # 2. Patient Cohort Screening Analysis
        md.append("\n## 2. Patient Cohort Screening Analysis")
        md.append(f"| Metric | Count | Percentage |")
        md.append(f"| :--- | :--- | :--- |")
        md.append(f"| Total Patients Screened | {scr.total_screened} | 100.0% |")
        md.append(f"| Confirmed Eligible | {scr.eligible_count} | {round(scr.eligibility_rate*100, 1)}% |")
        md.append(f"| Ineligible | {scr.ineligible_count} | {round((scr.ineligible_count/max(1, scr.total_screened))*100, 1)}% |")
        md.append(f"| Uncertain / Pending Review | {scr.uncertain_count} | {round(scr.uncertain_rate*100, 1)}% |")
        md.append(f"| Missing Clinical Data Rate | {scr.missing_data_count} | {round(scr.missing_data_rate*100, 1)}% |")

        if scr.top_exclusion_reasons:
            md.append("\n### Primary Exclusion Reasons")
            for crit, count in scr.top_exclusion_reasons.items():
                md.append(f"- **{crit}**: {count} patients disqualified")

        if scr.top_failed_inclusion_reasons:
            md.append("\n### Primary Failed Inclusion Criteria")
            for crit, count in scr.top_failed_inclusion_reasons.items():
                md.append(f"- **{crit}**: {count} patients did not meet threshold")

        # 3. Recruitment Forecast
        md.append("\n## 3. Deterministic Recruitment Forecast")
        md.append(f"- **Target Evaluated Enrollment:** {forecast.target_enrollment} patients")
        md.append(f"- **Required Screenings (Friction-Adjusted):** ~{forecast.target_enrollment + forecast.expected_screen_failures} patients (reflecting {forecast.expected_screen_failures} expected screen failures)")
        md.append(f"- **Anticipated Dropout Impact:** {forecast.expected_dropout_impact} subjects")
        md.append(f"- **Projected Shortfall by Deadline:** {forecast.recruitment_shortfall} patients")
        md.append(f"- **P10 Scenario (Optimistic):** {forecast.p10_time_months} months")
        md.append(f"- **P50 Scenario (Expected):** {forecast.p50_time_months} months")
        md.append(f"- **P90 Scenario (Conservative):** {forecast.p90_time_months} months")

        # 4. Candidate Trial Site Prioritization & Ranking
        md.append("\n## 4. Candidate Trial Site Prioritization & Ranking")
        md.append("| Rank | Site Name | Priority Score | Conf | Exp (Yrs) | Monthly Pts | Risk Level | Status |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        risk_map = {r.site_id: r for r in result.site_risks}
        for rank_item in result.site_rankings:
            site_risk = risk_map.get(rank_item.site_id)
            rl = site_risk.risk_level.value if site_risk else "N/A"
            flag = "FLAGGED FOR REVIEW" if rank_item.requires_review else "RECOMMENDED"
            md.append(
                f"| #{rank_item.rank} | {rank_item.site_name} (`{rank_item.site_id}`) | "
                f"**{rank_item.priority_score}** | {int(rank_item.confidence*100)}% | "
                f"{rank_item.recruitment_estimate_monthly} mo | {rl} | {flag} |"
            )

        # 5. Site Strengths, Weaknesses & Rationale Detail
        md.append("\n### Site Detailed Profiles")
        for rank_item in result.site_rankings[:5]:
            md.append(f"#### #{rank_item.rank}: {rank_item.site_name} (`{rank_item.site_id}`)")
            md.append(f"- **Score:** {rank_item.priority_score}/100 (Confidence: {int(rank_item.confidence*100)}%)")
            md.append(f"- **Rationale:** {rank_item.rationale}")
            md.append(f"- **Strengths:** {', '.join(rank_item.strengths)}")
            if rank_item.weaknesses:
                md.append(f"- **Weaknesses:** {', '.join(rank_item.weaknesses)}")
            if rank_item.risk_flags:
                md.append(f"- **Risk Flags:** {', '.join(rank_item.risk_flags)}")

        # 6. Protocol Deviation & Compliance Analysis
        md.append("\n## 5. Protocol Deviation & Compliance Monitoring")
        md.append("### Empirical Facts:")
        for fact in devs.facts:
            md.append(f"- {fact}")
        md.append("### Analytical Risk Interpretations:")
        for interp in devs.interpretations:
            md.append(f"- {interp}")

        # 7. Human Review Decisions
        md.append("\n## 6. Human-In-The-Loop Audit & Governance")
        if result.human_reviews:
            md.append("| Review ID | Item Type | Item ID | Reviewer | Decision | Notes |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for h in result.human_reviews:
                md.append(f"| {h.review_id} | {h.item_type.value} | {h.item_id} | {h.reviewer_id} | **{h.decision.value}** | {h.justification_notes} |")
        else:
            md.append("No manual human overrides or reviews recorded in this execution run.")

        # 8. Methodology and System Limitations
        md.append("\n## 7. Methodology & Mathematical Foundation")
        md.append(
            "- **Eligibility Evaluation:** Deterministic rule execution outside LLMs. No probabilistic guesswork for clinical thresholds.\n"
            "- **Multi-Criteria Site Scoring (MCDA):** 0-100 normalized composite: "
            "30% Recruitment Velocity, 20% Operations, 20% Investigator Experience, 15% Data Quality, 15% Compliance, "
            "with calibrated penalty deductions for multi-dimensional risks.\n"
            "- **Forecasting Methodology:** Non-linear queuing and friction adjustments accounting for screen failure rate and dropout attrition.\n"
        )
        md.append("## 8. Limitations & Scope of Demonstration")
        md.append(
            "1. **Synthetic Nature:** All patients, investigator metrics, and deviations are synthetic artifacts generated for simulation.\n"
            "2. **Decision-Support Only:** This system produces recommendations to assist trial operations personnel and CROs. "
            "It does not make autonomous clinical trial decisions without certified human review."
        )

        return "\n".join(md)

    def generate_json_report(self, result: TrialAnalysisResult) -> str:
        """Serializes complete trial analysis result to structured JSON."""
        return result.model_dump_json(indent=2)

    def generate_patients_csv(self, result: TrialAnalysisResult) -> str:
        """Exports patient screening results to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "patient_id", "status", "confidence", "requires_human_review",
            "matched_inclusion_count", "failed_inclusion_count",
            "triggered_exclusion_count", "missing_information_count", "explanation"
        ])
        for r in result.patient_screening_results:
            writer.writerow([
                r.patient_id,
                r.status.value,
                r.confidence,
                r.requires_human_review,
                len(r.matched_inclusion),
                len(r.failed_inclusion),
                len(r.triggered_exclusion),
                len(r.missing_information),
                r.explanation.replace("\n", " | "),
            ])
        return output.getvalue()

    def generate_sites_csv(self, result: TrialAnalysisResult) -> str:
        """Exports site rankings and risk scores to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "rank", "site_id", "site_name", "priority_score", "confidence",
            "recruitment_monthly", "overall_risk_score", "risk_level",
            "requires_review", "strengths", "weaknesses", "risk_flags"
        ])
        risk_map = {r.site_id: r for r in result.site_risks}
        for r in result.site_rankings:
            site_risk = risk_map.get(r.site_id)
            writer.writerow([
                r.rank,
                r.site_id,
                r.site_name,
                r.priority_score,
                r.confidence,
                r.recruitment_estimate_monthly,
                site_risk.overall_risk_score if site_risk else 0.0,
                site_risk.risk_level.value if site_risk else "N/A",
                r.requires_review,
                "; ".join(r.strengths),
                "; ".join(r.weaknesses),
                "; ".join(r.risk_flags),
            ])
        return output.getvalue()

    def generate_deviations_csv(self, result: TrialAnalysisResult) -> str:
        """Exports protocol deviations to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "deviation_id", "site_id", "trial_id", "category", "severity",
            "occurrence_date", "resolved", "recurrence", "description"
        ])
        for d in result.deviations:
            writer.writerow([
                d.deviation_id,
                d.site_id,
                d.trial_id,
                d.category.value,
                d.severity.value,
                d.occurrence_date,
                d.resolved,
                d.recurrence,
                d.description,
            ])
        return output.getvalue()


report_generator = ExecutiveReportGenerator()
