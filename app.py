"""Streamlit Executive Dashboard: Clinical Trial Site Selection & Recruitment Agent.

A production-quality Agentic AI decision-support platform for clinical trial feasibility,
deterministic eligibility screening, protocol deviation detection, and multi-criteria site ranking.

SYNTHETIC DEMONSTRATION DATA ONLY.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.config import config, DISCLAIMER_TEXT, RiskScoringWeights, SiteRankingWeights
from src.domain.models import (
    Trial,
    EligibilityStatus,
    HumanDecisionType,
    RiskLevel,
    ReviewItemType,
)
from src.providers.synthetic_data_generator import SyntheticDataProvider
from src.workflow.orchestrator import TrialWorkflowOrchestrator
from src.engines import SiteRiskEngine, SiteRankingEngine
from src.agents.human_review_agent import human_review_agent
from src.reporting.report_generator import report_generator
from src.audit.audit_trail import audit_logger
from src.ui.visualizations import (
    plot_eligibility_funnel,
    plot_exclusion_reasons,
    plot_geographic_distribution,
    plot_site_rankings,
    plot_enrollment_projection,
    plot_deviation_breakdown,
    plot_site_risk_heatmap,
    plot_site_radar,
)
from src.agents.patient_screening_agent import patient_screening_agent


# Page Configuration
st.set_page_config(
    page_title="Clinical Trial Site Selection & Recruitment Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Enterprise Medical UI
st.markdown(
    """
    <style>
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .disclaimer-box {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 0.85rem 1.1rem;
        margin-bottom: 1.2rem;
        border-radius: 4px;
        color: #991b1b;
        font-size: 0.88rem;
    }
    .stat-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .stat-number {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    .stat-label {
        font-size: 0.82rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-title">🏥 Clinical Trial Site Selection & Recruitment Agent</div>', unsafe_allow_html=True)
st.caption("AI-Assisted Multi-Agent Clinical Decision-Support Platform | Deterministic Feasibility & Site Prioritization")


# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/color/96/clinical-fe.png", width=64)
st.sidebar.title("Trial Parameters")

provider = SyntheticDataProvider()
available_trials = provider.get_trials()
trial_options = {f"{t.trial_id} - {t.therapeutic_area} ({t.phase})": t for t in available_trials}

selected_trial_key = st.sidebar.selectbox("Select Protocol", list(trial_options.keys()))
active_trial = trial_options[selected_trial_key]

st.sidebar.markdown("---")
st.sidebar.subheader("Cohort & Simulation Settings")
cohort_size = st.sidebar.slider("Synthetic Patient Pool Size", min_value=50, max_value=500, value=250, step=25)
random_seed = st.sidebar.number_input("Random Generator Seed", min_value=1, max_value=9999, value=42)

# Weight Adjustments
with st.sidebar.expander("⚙️ Deterministic Scoring Weights"):
    st.write("**Risk Engine Weights:**")
    w_rec = st.slider("Recruitment Risk Weight", 0.05, 0.50, 0.25, 0.05)
    w_comp = st.slider("Compliance Risk Weight", 0.05, 0.50, 0.20, 0.05)
    w_dq = st.slider("Data Quality Weight", 0.05, 0.40, 0.15, 0.05)
    w_exp = 0.15
    w_ops = 0.15
    w_cap = max(0.05, round(1.0 - (w_rec + w_comp + w_dq + w_exp + w_ops), 2))
    custom_risk_weights = RiskScoringWeights(
        recruitment_weight=w_rec,
        compliance_weight=w_comp,
        data_quality_weight=w_dq,
        investigator_experience_weight=w_exp,
        operational_weight=w_ops,
        capacity_activation_weight=w_cap,
    )

rerun_pipeline = st.sidebar.button("🚀 Re-Run Multi-Agent Pipeline", use_container_width=True)

# State initialization and pipeline execution
state_key = f"analysis_{active_trial.trial_id}_{cohort_size}_{random_seed}_{w_rec}_{w_comp}_{w_dq}"

if rerun_pipeline or state_key not in st.session_state:
    with st.spinner("Executing Multi-Agent LangGraph Workflow..."):
        # Generate fresh cohort matching parameters
        custom_provider = SyntheticDataProvider(seed=random_seed)
        sites = custom_provider.get_sites()
        patients = custom_provider.generator.generate_patients(count=cohort_size, sites=sites)
        deviations = custom_provider.get_deviations(trial_id=active_trial.trial_id)
        if not deviations:
            deviations = custom_provider.generator.generate_deviations(sites=sites, trial_id=active_trial.trial_id)

        custom_risk_engine = SiteRiskEngine(weights=custom_risk_weights)
        orchestrator = TrialWorkflowOrchestrator(risk_engine=custom_risk_engine)
        analysis = orchestrator.run(
            trial=active_trial,
            patients=patients,
            sites=sites,
            deviations=deviations,
        )
        st.session_state[state_key] = analysis
        st.session_state["active_patients"] = patients
        st.session_state["active_sites"] = sites

analysis_result = st.session_state[state_key]
patients = st.session_state.get("active_patients", [])
sites = st.session_state.get("active_sites", [])


# Main Navigation Tabs (12 Comprehensive Modules)
tabs = st.tabs([
    "1. Executive Summary",
    "2. Trial Overview",
    "3. Patient Recruitment",
    "4. Eligibility Screening",
    "5. Site Intelligence",
    "6. Site Ranking",
    "7. Recruitment Forecast",
    "8. Protocol Deviations",
    "9. Risk & Data Quality",
    "10. Human Review Console",
    "11. Agent Audit Trace",
    "12. Reports & Export",
])


# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tabs[0]:
    st.subheader("Executive Trial Feasibility Summary")
    st.caption("Consolidated outputs from multi-agent evaluation and deterministic decision engines.")

    scr = analysis_result.screening_summary
    forecast = analysis_result.recruitment_forecast
    top_site = analysis_result.site_rankings[0] if analysis_result.site_rankings else None
    high_risk_sites = [r for r in analysis_result.site_risks if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Target Enrollment</div>
                <div class="stat-number">{active_trial.target_enrollment}</div>
                <small>Deadline: {active_trial.enrollment_deadline}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Eligible Patient Pool</div>
                <div class="stat-number">{scr.eligible_count}</div>
                <small>{round(scr.eligibility_rate * 100, 1)}% of screened cohort</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Expected Monthly Rate</div>
                <div class="stat-number">{forecast.expected_monthly_enrollment}</div>
                <small>patients / month active</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        top_name = top_site.site_name[:20] + "..." if top_site and len(top_site.site_name) > 20 else "N/A"
        top_score = top_site.priority_score if top_site else 0
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Top Candidate Site</div>
                <div class="stat-number">{top_score}/100</div>
                <small>{top_name}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        avg_risk = round(sum(r.overall_risk_score for r in analysis_result.site_risks) / max(1, len(analysis_result.site_risks)), 1)
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Average Site Risk</div>
                <div class="stat-number">{avg_risk}</div>
                <small>Score 0 (Safe) to 100 (Critical)</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">High-Risk Sites</div>
                <div class="stat-number">{len(high_risk_sites)}</div>
                <small>Requiring GCP oversight</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c7:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Protocol Deviations</div>
                <div class="stat-number">{analysis_result.deviation_summary.total_deviations}</div>
                <small>{analysis_result.deviation_summary.unresolved_count} unresolved backlog</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Projected Timeline (P50)</div>
                <div class="stat-number">{forecast.p50_time_months} mo</div>
                <small>Probability: {int(forecast.enrollment_probability * 100)}%</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # High level visualizations
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.plotly_chart(plot_site_rankings(analysis_result.site_rankings), use_container_width=True, key="exec_tab_site_rankings")
    with col_b:
        st.plotly_chart(plot_enrollment_projection(forecast), use_container_width=True, key="exec_tab_enrollment_curve")


# ==========================================
# TAB 2: TRIAL OVERVIEW
# ==========================================
with tabs[1]:
    st.subheader(f"Protocol Specification: {active_trial.trial_name}")
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(
            f"""
            - **Protocol Identifier:** `{active_trial.trial_id}`
            - **Therapeutic Area:** {active_trial.therapeutic_area}
            - **Development Phase:** {active_trial.phase}
            - **Target Population:** {active_trial.target_population}
            - **Target Enrolled Patients:** {active_trial.target_enrollment} evaluable subjects
            - **Protocol Version:** {active_trial.protocol_version}
            - **Target Completion Deadline:** `{active_trial.enrollment_deadline}`
            """
        )
    with col_t2:
        st.info(
            f"**Decision Support Status:**\n\n"
            f"Machine-readable rules loaded:\n"
            f"- **{len(active_trial.inclusion_criteria)}** Inclusion Criteria\n"
            f"- **{len(active_trial.exclusion_criteria)}** Exclusion Criteria\n"
            f"- **All criteria verified deterministic**."
        )

    st.markdown("### Structured Inclusion Criteria")
    inc_df = pd.DataFrame([
        {
            "ID": c.criterion_id,
            "Category": c.category.value,
            "Field": c.field_name,
            "Operator": c.operator,
            "Target Value": str(c.target_value),
            "Clinical Description": c.description,
        }
        for c in active_trial.inclusion_criteria
    ])
    st.dataframe(inc_df, use_container_width=True, hide_index=True)

    st.markdown("### Structured Exclusion Criteria")
    exc_df = pd.DataFrame([
        {
            "ID": c.criterion_id,
            "Category": c.category.value,
            "Field": c.field_name,
            "Operator": c.operator,
            "Target Value": str(c.target_value),
            "Clinical Description": c.description,
        }
        for c in active_trial.exclusion_criteria
    ])
    st.dataframe(exc_df, use_container_width=True, hide_index=True)


# ==========================================
# TAB 3: PATIENT RECRUITMENT
# ==========================================
with tabs[2]:
    st.subheader("Patient Cohort Distribution & Regional Pools")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.plotly_chart(plot_eligibility_funnel(analysis_result.screening_summary), use_container_width=True, key="recruitment_tab_funnel")
    with col_p2:
        geo_dict = patient_screening_agent.get_geographic_distribution(
            patients, analysis_result.patient_screening_results
        )
        st.plotly_chart(plot_geographic_distribution(geo_dict), use_container_width=True, key="recruitment_tab_geo")

    st.markdown("### Recruitment Pool by Candidate Site")
    site_breakdown = patient_screening_agent.get_candidate_breakdown_by_site(
        patients, analysis_result.patient_screening_results
    )
    site_df = pd.DataFrame([
        {
            "Site ID": sid,
            "Total Local Pool Screened": data["total"],
            "Eligible Candidates": data["eligible"],
            "Uncertain (Pending Review)": data["uncertain"],
            "Ineligible": data["ineligible"],
            "Conversion Potential": f"{round((data['eligible']/max(1, data['total']))*100, 1)}%",
        }
        for sid, data in site_breakdown.items()
    ])
    st.dataframe(site_df, use_container_width=True, hide_index=True)


# ==========================================
# TAB 4: ELIGIBILITY SCREENING
# ==========================================
with tabs[3]:
    st.subheader("Patient-Level Deterministic Eligibility Screening")
    st.caption("Every patient evaluation is computed using deterministic logic with full audit provenance.")

    filter_status = st.selectbox("Filter Status", ["ALL", "ELIGIBLE", "INELIGIBLE", "UNCERTAIN"], key="screening_filter_status")

    res_list = analysis_result.patient_screening_results
    if filter_status != "ALL":
        res_list = [r for r in res_list if r.status.value == filter_status]

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        st.plotly_chart(plot_exclusion_reasons(analysis_result.screening_summary), use_container_width=True, key="screening_tab_exclusions")
    with col_s2:
        st.markdown(
            f"""
            **Screening Population Diagnostics:**
            - Total Screened: **{analysis_result.screening_summary.total_screened}**
            - Matched Eligible: **{analysis_result.screening_summary.eligible_count}** ({round(analysis_result.screening_summary.eligibility_rate*100, 1)}%)
            - Flagged Uncertain: **{analysis_result.screening_summary.uncertain_count}** ({round(analysis_result.screening_summary.uncertain_rate*100, 1)}%)
            - Disqualified Ineligible: **{analysis_result.screening_summary.ineligible_count}**
            - Missing Clinical Data Points: **{analysis_result.screening_summary.missing_data_count}**
            """
        )

    # Detailed patient table
    pt_table_data = [
        {
            "Patient ID": r.patient_id,
            "Eligibility Status": r.status.value,
            "Confidence": f"{int(r.confidence * 100)}%",
            "Matched Inclusions": len(r.matched_inclusion),
            "Failed Inclusions": len(r.failed_inclusion),
            "Triggered Exclusions": len(r.triggered_exclusion),
            "Missing Info": len(r.missing_information),
            "Requires Review": "YES" if r.requires_human_review else "NO",
        }
        for r in res_list
    ]
    st.dataframe(pd.DataFrame(pt_table_data), use_container_width=True, hide_index=True)

    with st.expander("🔍 Inspect Individual Patient Clinical Rationale"):
        pt_options = [r.patient_id for r in res_list[:50]]
        if pt_options:
            selected_pt_id = st.selectbox("Select Patient", pt_options, key="screening_select_pt_inspect")
            matched_pt = next((r for r in res_list if r.patient_id == selected_pt_id), None)
            if matched_pt:
                st.markdown(f"**Patient ID:** `{matched_pt.patient_id}` | **Status:** `{matched_pt.status.value}` (Confidence: {int(matched_pt.confidence*100)}%)")
                st.text_area("Screening Explanation & Provenance", matched_pt.explanation, height=140, key=f"screening_expl_{matched_pt.patient_id}")
        else:
            st.caption("No patients match the current filter selection.")


# ==========================================
# TAB 5: SITE INTELLIGENCE
# ==========================================
with tabs[4]:
    st.subheader("Site Intelligence & Historical Performance Profiles")
    st.caption("Multi-dimensional operational metrics scored without LLM hallucination.")

    perfs = analysis_result.site_performances
    perf_df = pd.DataFrame([
        {
            "Site ID": p.site_id,
            "Site Name": p.site_name,
            "Composite Score": p.composite_performance_score,
            "Enrollment Velocity": p.enrollment_velocity_score,
            "Experience": p.experience_score,
            "Compliance": p.compliance_score,
            "Data Quality": p.data_quality_score,
            "Operations": p.operational_efficiency_score,
            "Capacity": p.capacity_score,
        }
        for p in perfs
    ])
    st.dataframe(perf_df, use_container_width=True, hide_index=True)

    st.markdown("### Site Operational Radar Profiling")
    selected_site_radar = st.selectbox("Select Site for Radar Analysis", [p.site_name for p in perfs], key="intel_select_site_radar")
    matched_perf = next((p for p in perfs if p.site_name == selected_site_radar), perfs[0])
    st.plotly_chart(plot_site_radar(matched_perf), use_container_width=True, key="intel_tab_site_radar")


# ==========================================
# TAB 6: SITE RANKING
# ==========================================
with tabs[5]:
    st.subheader("Candidate Site Prioritization & Ranking (MCDA)")
    st.caption("Normalized 0-100 composite priority scores with grounded strengths, weaknesses, and risk penalties.")

    st.plotly_chart(plot_site_rankings(analysis_result.site_rankings), use_container_width=True, key="ranking_tab_site_rankings")

    for rank_item in analysis_result.site_rankings:
        with st.expander(f"Rank #{rank_item.rank}: {rank_item.site_name} — Score {rank_item.priority_score}/100"):
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                st.markdown(f"**Rationale:** {rank_item.rationale}")
                st.markdown(f"- **Key Strengths:** {', '.join(rank_item.strengths)}")
                if rank_item.weaknesses:
                    st.markdown(f"- **Areas for Improvement:** {', '.join(rank_item.weaknesses)}")
            with col_r2:
                st.metric("Priority Score", f"{rank_item.priority_score} / 100")
                st.metric("Recruitment Capacity", f"~{rank_item.recruitment_estimate_monthly} pts/mo")
                st.metric("Confidence", f"{int(rank_item.confidence * 100)}%")
                if rank_item.requires_review:
                    st.warning("⚠️ Flagged for Human Review")


# ==========================================
# TAB 7: RECRUITMENT FORECAST
# ==========================================
with tabs[6]:
    st.subheader("Recruitment Forecasting & Horizon Analysis")
    st.caption("Mathematical projections incorporating screen failures, dropout attrition, and multi-scenario uncertainty.")

    st.plotly_chart(plot_enrollment_projection(analysis_result.recruitment_forecast), use_container_width=True, key="forecast_tab_enrollment_curve")

    fc = analysis_result.recruitment_forecast
    c_fc1, c_fc2, c_fc3, c_fc4 = st.columns(4)
    c_fc1.metric("Optimistic (P10)", f"{fc.p10_time_months} months")
    c_fc2.metric("Expected (P50)", f"{fc.p50_time_months} months")
    c_fc3.metric("Conservative (P90)", f"{fc.p90_time_months} months")
    c_fc4.metric("Enrollment Probability", f"{int(fc.enrollment_probability * 100)}%")

    st.markdown("### Projection Friction & Attrition Drivers")
    col_fc_a, col_fc_b = st.columns(2)
    with col_fc_a:
        st.markdown(
            f"""
            - **Target Evaluated Cohort:** {fc.target_enrollment} patients
            - **Expected Screen Failures:** ~{fc.expected_screen_failures} patients
            - **Anticipated Dropout Impact:** {fc.expected_dropout_impact} subjects
            - **Projected Recruitment Shortfall:** {fc.recruitment_shortfall} subjects
            """
        )
    with col_fc_b:
        st.json(fc.assumptions)


# ==========================================
# TAB 8: PROTOCOL DEVIATIONS
# ==========================================
with tabs[7]:
    st.subheader("Protocol Deviation Monitoring & GCP Compliance")
    st.caption("Rigorous separation between verifiable empirical clinical facts and analytical risk interpretations.")

    dev_sum = analysis_result.deviation_summary
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        st.plotly_chart(plot_deviation_breakdown(dev_sum), use_container_width=True, key="deviations_tab_severity_breakdown")
    with col_d2:
        st.markdown("### Verifiable Empirical Facts:")
        for fact in dev_sum.facts:
            st.success(fact)
        st.markdown("### Analytical Risk Interpretations:")
        for interp in dev_sum.interpretations:
            st.warning(interp)

    st.markdown("### Recorded Deviation Log (Synthetic Audit Trail)")
    dev_table = [
        {
            "Deviation ID": d.deviation_id,
            "Site ID": d.site_id,
            "Category": d.category.value,
            "Severity": d.severity.value,
            "Occurrence Date": d.occurrence_date,
            "Resolved": "YES" if d.resolved else "NO (OPEN)",
            "Recurrence": "YES" if d.recurrence else "NO",
            "Description": d.description,
        }
        for d in analysis_result.deviations[:40]
    ]
    st.dataframe(pd.DataFrame(dev_table), use_container_width=True, hide_index=True)


# ==========================================
# TAB 9: RISK & DATA QUALITY
# ==========================================
with tabs[8]:
    st.subheader("Multi-Dimensional Site Risk & Data Quality Matrix")
    st.caption("Configurable, fully disclosed weighted risk calculations across 6 dimensions.")

    st.plotly_chart(plot_site_risk_heatmap(analysis_result.site_risks), use_container_width=True, key="risk_tab_site_heatmap")

    risk_df = pd.DataFrame([
        {
            "Site ID": r.site_id,
            "Site Name": r.site_name,
            "Overall Risk Score": r.overall_risk_score,
            "Risk Level": r.risk_level.value,
            "Recruitment Risk": r.recruitment_risk,
            "Compliance Risk": r.compliance_risk,
            "Data Quality Risk": r.data_quality_risk,
            "Operational Risk": r.operational_risk,
            "Capacity Risk": r.capacity_risk,
            "Activation Risk": r.activation_risk,
            "Escalate to Review": "YES" if r.requires_human_review else "NO",
        }
        for r in analysis_result.site_risks
    ])
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

    with st.expander("📐 Mathematical Formula & Weight Transparency"):
        selected_risk_site = st.selectbox("Inspect Site Mathematical Breakdown", [r.site_name for r in analysis_result.site_risks], key="risk_select_site_breakdown")
        matched_r = next((r for r in analysis_result.site_risks if r.site_name == selected_risk_site), analysis_result.site_risks[0])
        st.write(f"**Mathematical Formula:** `{matched_r.mathematical_breakdown.get('formula')}`")
        st.json(matched_r.mathematical_breakdown)


# ==========================================
# TAB 10: HUMAN REVIEW CONSOLE
# ==========================================
with tabs[9]:
    st.subheader("Human-In-The-Loop Governance Console")
    st.caption("AI-assisted recommendations require clinical confirmation for borderline or high-risk cases.")

    pending = human_review_agent.identify_pending_reviews(
        analysis_result.patient_screening_results,
        analysis_result.site_risks,
        analysis_result.site_rankings,
    )

    col_hr1, col_hr2 = st.columns(2)
    with col_hr1:
        st.metric("Patients Requiring Clinical Review", len(pending["patients"]))
    with col_hr2:
        st.metric("Sites Requiring Operational Review", len(pending["site_rankings"]))

    st.markdown("---")

    # Review Action Section
    review_target_type = st.radio("Review Queue", ["Uncertain Patient Cases", "Flagged Candidate Sites"], horizontal=True, key="hitl_review_target_type")

    if review_target_type == "Uncertain Patient Cases":
        if not pending["patients"]:
            st.success("No patient screening results currently require human escalation.")
        else:
            pt_to_review = st.selectbox(
                "Select Patient for Review",
                [p.patient_id for p in pending["patients"]],
                key="hitl_select_pt_to_review"
            )
            matched_pt = next(p for p in pending["patients"] if p.patient_id == pt_to_review)
            st.info(f"**Current AI Assessment:** {matched_pt.status.value} (Confidence: {int(matched_pt.confidence*100)}%)\n\n{matched_pt.explanation}")

            with st.form("patient_review_form"):
                reviewer_id = st.text_input("Investigator / Reviewer ID", value="MD-INVESTIGATOR-01", key="hitl_pt_reviewer_id")
                decision_choice = st.selectbox("Review Decision", [d.value for d in HumanDecisionType], key="hitl_pt_decision_choice")
                override_opt = st.selectbox("Override Status (if MODIFY)", [s.value for s in EligibilityStatus], key="hitl_pt_override_opt")
                justification = st.text_area("Clinical Justification & Notes", placeholder="Provide rationale for override or approval based on protocol waiver or confirmatory test...", key="hitl_pt_justification")
                submit_pt_review = st.form_submit_button("Submit Clinical Decision")

                if submit_pt_review:
                    updated_pt, rev_dec = human_review_agent.record_patient_decision(
                        patient_result=matched_pt,
                        reviewer_id=reviewer_id,
                        decision=HumanDecisionType(decision_choice),
                        justification_notes=justification,
                        override_status=EligibilityStatus(override_opt) if decision_choice == "MODIFY" else None,
                    )
                    # Synchronize into analysis_result in session state
                    for idx, pt_item in enumerate(analysis_result.patient_screening_results):
                        if pt_item.patient_id == updated_pt.patient_id:
                            analysis_result.patient_screening_results[idx] = updated_pt
                            break
                    # Recalculate summary metrics
                    tot = len(analysis_result.patient_screening_results)
                    el_c = sum(1 for r in analysis_result.patient_screening_results if r.status == EligibilityStatus.ELIGIBLE)
                    in_c = sum(1 for r in analysis_result.patient_screening_results if r.status == EligibilityStatus.INELIGIBLE)
                    un_c = sum(1 for r in analysis_result.patient_screening_results if r.status == EligibilityStatus.UNCERTAIN)
                    analysis_result.screening_summary.eligible_count = el_c
                    analysis_result.screening_summary.ineligible_count = in_c
                    analysis_result.screening_summary.uncertain_count = un_c
                    analysis_result.screening_summary.eligibility_rate = round(el_c / max(1, tot), 4)
                    analysis_result.screening_summary.uncertain_rate = round(un_c / max(1, tot), 4)
                    analysis_result.human_reviews.append(rev_dec)

                    st.success(f"Decision recorded successfully: {rev_dec.review_id}")
                    st.rerun()

    else:
        if not pending["site_rankings"]:
            st.success("No candidate sites currently flagged for operational escalation.")
        else:
            site_to_review = st.selectbox(
                "Select Site for Review",
                [s.site_name for s in pending["site_rankings"]],
                key="hitl_select_site_to_review"
            )
            matched_s = next(s for s in pending["site_rankings"] if s.site_name == site_to_review)
            st.warning(f"**Current Priority:** {matched_s.priority_score}/100 | **Risk Flags:** {', '.join(matched_s.risk_flags)}")

            with st.form("site_review_form"):
                reviewer_id = st.text_input("Clinical Operations Director ID", value="CRO-DIRECTOR-01", key="hitl_site_reviewer_id")
                decision_choice = st.selectbox("Review Decision", [d.value for d in HumanDecisionType], key="hitl_site_decision_choice")
                new_score = st.slider("Adjusted Priority Score (if MODIFY)", 0.0, 100.0, float(matched_s.priority_score), 1.0, key="hitl_site_new_score")
                justification = st.text_area("Operational Justification & Mitigation Plan", placeholder="Document risk mitigation, enhanced monitoring visits, or GCP re-training...", key="hitl_site_justification")
                submit_site_review = st.form_submit_button("Submit Site Decision")

                if submit_site_review:
                    updated_s, rev_dec = human_review_agent.record_site_decision(
                        ranking_item=matched_s,
                        reviewer_id=reviewer_id,
                        decision=HumanDecisionType(decision_choice),
                        justification_notes=justification,
                        override_priority_score=new_score if decision_choice == "MODIFY" else None,
                    )
                    # Synchronize into analysis_result in session state
                    for idx, s_item in enumerate(analysis_result.site_rankings):
                        if s_item.site_id == updated_s.site_id:
                            analysis_result.site_rankings[idx] = updated_s
                            break
                    # Re-sort descending by priority score and re-rank
                    analysis_result.site_rankings.sort(key=lambda x: x.priority_score, reverse=True)
                    for r_idx, s_item in enumerate(analysis_result.site_rankings, start=1):
                        s_item.rank = r_idx
                    analysis_result.human_reviews.append(rev_dec)

                    st.success(f"Site review recorded successfully: {rev_dec.review_id}")
                    st.rerun()

    st.markdown("### Human Decision History")
    if human_review_agent.decision_history:
        history_df = pd.DataFrame([
            {
                "Review ID": h.review_id,
                "Item Type": h.item_type.value,
                "Item ID": h.item_id,
                "Reviewer": h.reviewer_id,
                "Decision": h.decision.value,
                "Timestamp": h.timestamp,
                "Notes": h.justification_notes,
                "Overrides": str(h.override_values),
            }
            for h in human_review_agent.decision_history
        ])
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No manual overrides or reviews recorded yet.")


# ==========================================
# TAB 11: AGENT AUDIT TRACE
# ==========================================
with tabs[10]:
    st.subheader("Multi-Agent Execution Audit & Provenance Trace")
    st.caption("Immutable chronological record of every agent action, node state transition, and confidence score.")

    events = audit_logger.get_events()
    agent_filter = st.selectbox("Filter Agent / Node", ["ALL"] + sorted(list(set(e.agent_or_node for e in events))), key="audit_filter_agent")

    filtered_events = events if agent_filter == "ALL" else [e for e in events if e.agent_or_node == agent_filter]

    audit_table_data = [
        {
            "Event ID": e.event_id,
            "Timestamp": e.timestamp,
            "Agent / Node": e.agent_or_node,
            "Action": e.action,
            "Decision": e.decision,
            "Confidence": f"{int(e.confidence * 100)}%" if e.confidence is not None else "-",
            "Latency (ms)": e.execution_latency_ms,
            "Provenance": e.data_provenance,
            "Warnings": len(e.warnings),
        }
        for e in filtered_events
    ]
    st.dataframe(pd.DataFrame(audit_table_data), use_container_width=True, hide_index=True)

    with st.expander("🔍 Inspect Full Event Payload"):
        if filtered_events:
            sel_evt_id = st.selectbox("Select Event ID", [e.event_id for e in filtered_events], key="audit_select_event_id")
            matched_evt = next((e for e in filtered_events if e.event_id == sel_evt_id), None)
            if matched_evt:
                st.json(matched_evt.model_dump())
        else:
            st.caption("No events recorded for this selection.")


# ==========================================
# TAB 12: REPORTS & EXPORT
# ==========================================
with tabs[11]:
    st.subheader("Executive Reports & Machine-Readable Data Export")
    st.caption("Download comprehensive Markdown dossier, structured JSON, or tabular CSV outputs.")

    md_report = report_generator.generate_markdown_report(analysis_result)
    json_report = report_generator.generate_json_report(analysis_result)
    patients_csv = report_generator.generate_patients_csv(analysis_result)
    sites_csv = report_generator.generate_sites_csv(analysis_result)
    deviations_csv = report_generator.generate_deviations_csv(analysis_result)

    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
    with col_exp1:
        st.download_button(
            "📄 Download Markdown Report",
            data=md_report,
            file_name=f"trial_feasibility_report_{active_trial.trial_id}.md",
            mime="text/markdown",
            use_container_width=True,
            key="export_download_md",
        )
    with col_exp2:
        st.download_button(
            "💾 Download JSON Result",
            data=json_report,
            file_name=f"trial_analysis_{active_trial.trial_id}.json",
            mime="application/json",
            use_container_width=True,
            key="export_download_json",
        )
    with col_exp3:
        st.download_button(
            "📊 Download Patients CSV",
            data=patients_csv,
            file_name="synthetic_patient_screening.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_download_patients_csv",
        )
    with col_exp4:
        st.download_button(
            "🏥 Download Sites CSV",
            data=sites_csv,
            file_name="site_rankings_and_risks.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_download_sites_csv",
        )

    st.markdown("---")
    st.markdown("### Executive Report Markdown Preview")
    st.markdown(md_report)
