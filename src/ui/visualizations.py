"""Plotly Visualizations for Clinical Trial Site Selection Dashboard.

All charts explicitly display synthetic demonstration labels.
"""

from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from src.domain.models import (
    PatientScreeningSummary,
    RecruitmentForecast,
    ProtocolDeviationSummary,
    SiteRanking,
    SiteRisk,
    SitePerformance,
)


def plot_eligibility_funnel(summary: PatientScreeningSummary) -> go.Figure:
    """Funnel chart of cohort screening outcomes."""
    fig = go.Figure(
        go.Funnel(
            y=["Total Screened", "Eligible Pool", "Uncertain / Review", "Ineligible"],
            x=[
                summary.total_screened,
                summary.eligible_count,
                summary.uncertain_count,
                summary.ineligible_count,
            ],
            textinfo="value+percent initial",
            marker={
                "color": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"],
            },
        )
    )
    fig.update_layout(
        title="Patient Screening Funnel (Synthetic Demo Data)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=340,
    )
    return fig


def plot_exclusion_reasons(summary: PatientScreeningSummary) -> go.Figure:
    """Horizontal bar chart of primary exclusion reasons."""
    reasons = summary.top_exclusion_reasons
    if not reasons:
        reasons = {"No triggered exclusions": 0}

    keys = list(reasons.keys())
    vals = list(reasons.values())

    fig = go.Figure(
        go.Bar(
            x=vals,
            y=keys,
            orientation="h",
            marker=dict(color="#f43f5e"),
            text=vals,
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Top Triggered Exclusion Criteria (Synthetic Demo Data)",
        xaxis_title="Number of Disqualified Patients",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
        yaxis=dict(autorange="reversed"),
    )
    return fig


def plot_geographic_distribution(geo_data: Dict[str, Dict[str, int]]) -> go.Figure:
    """Bar chart of candidate pool distribution across geographic regions."""
    if not geo_data:
        fig = go.Figure()
        fig.add_annotation(text="No geographic data available (Synthetic Demo)", showarrow=False)
        fig.update_layout(title="Geographic Candidate Distribution", height=320)
        return fig

    regions = list(geo_data.keys())
    screened = [geo_data[r].get("screened", 0) for r in regions]
    eligible = [geo_data[r].get("eligible", 0) for r in regions]
    uncertain = [geo_data[r].get("uncertain", 0) for r in regions]

    fig = go.Figure(
        data=[
            go.Bar(name="Eligible", x=regions, y=eligible, marker_color="#10b981"),
            go.Bar(name="Uncertain", x=regions, y=uncertain, marker_color="#f59e0b"),
            go.Bar(name="Ineligible", x=regions, y=[s - e - u for s, e, u in zip(screened, eligible, uncertain)], marker_color="#94a3b8"),
        ]
    )
    fig.update_layout(
        barmode="stack",
        title="Geographic Candidate Distribution (Synthetic Demo Data)",
        yaxis_title="Patient Count",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_site_rankings(rankings: List[SiteRanking]) -> go.Figure:
    """Bar chart comparing prioritized site composite scores."""
    if not rankings:
        fig = go.Figure()
        fig.add_annotation(text="No candidate site rankings available", showarrow=False)
        fig.update_layout(title="Candidate Trial Sites Prioritized by MCDA", height=380)
        return fig

    top_n = rankings[:10]
    names = [f"#{r.rank} {r.site_name[:24]}..." if len(r.site_name) > 24 else f"#{r.rank} {r.site_name}" for r in top_n]
    scores = [r.priority_score for r in top_n]
    confs = [r.confidence * 100 for r in top_n]

    # Color gradient from green (high) to amber/red (low)
    colors = [
        "#10b981" if s >= 75 else "#3b82f6" if s >= 60 else "#f59e0b" if s >= 45 else "#ef4444"
        for s in scores
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=names,
            y=scores,
            marker_color=colors,
            text=[f"{s}/100" for s in scores],
            textposition="auto",
            hovertext=[f"Confidence: {int(c)}%" for c in confs],
            name="Priority Score",
        )
    )
    fig.update_layout(
        title="Candidate Trial Sites Prioritized by MCDA (Synthetic Demo Data)",
        yaxis_title="Priority Score (0 - 100)",
        xaxis_tickangle=-30,
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=80),
        height=380,
    )
    return fig


def plot_enrollment_projection(forecast: RecruitmentForecast) -> go.Figure:
    """Multi-scenario enrollment trajectory: P10 optimistic, P50 expected, P90 conservative."""
    target = forecast.target_enrollment
    p50_mo = max(1.0, forecast.p50_time_months)
    p10_mo = max(1.0, forecast.p10_time_months)
    p90_mo = max(1.0, forecast.p90_time_months)

    max_mo = int(np.ceil(p90_mo * 1.15))
    months = np.linspace(0, max_mo, 30)

    # Monthly rates
    rate_p50 = target / p50_mo
    rate_p10 = target / p10_mo
    rate_p90 = target / p90_mo

    curve_p50 = np.minimum(target, rate_p50 * months)
    curve_p10 = np.minimum(target, rate_p10 * months)
    curve_p90 = np.minimum(target, rate_p90 * months)

    fig = go.Figure()

    # Confidence band (between P90 and P10)
    fig.add_trace(
        go.Scatter(
            x=list(months) + list(months)[::-1],
            y=list(curve_p10) + list(curve_p90)[::-1],
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Uncertainty Range (P10 - P90)",
        )
    )

    # Target threshold line
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Target ({target} pts)",
        annotation_position="bottom right",
    )

    # Curves
    fig.add_trace(
        go.Scatter(
            x=months,
            y=curve_p10,
            mode="lines",
            line=dict(color="#10b981", dash="dot", width=2),
            name=f"P10 Optimistic ({p10_mo} mo)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=months,
            y=curve_p50,
            mode="lines",
            line=dict(color="#2563eb", width=3),
            name=f"P50 Expected ({p50_mo} mo)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=months,
            y=curve_p90,
            mode="lines",
            line=dict(color="#f59e0b", dash="dash", width=2),
            name=f"P90 Conservative ({p90_mo} mo)",
        )
    )

    fig.update_layout(
        title="Projected Enrollment Trajectory (Synthetic Demo Data)",
        xaxis_title="Months From Protocol Activation",
        yaxis_title="Enrolled Evaluated Patients",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_deviation_breakdown(summary: ProtocolDeviationSummary) -> go.Figure:
    """Pie/Donut chart of protocol deviations by severity."""
    sev = summary.severity_breakdown
    labels = [k.value if hasattr(k, "value") else str(k) for k in sev.keys()]
    values = list(sev.values())

    color_map = {
        "LOW": "#3b82f6",
        "MEDIUM": "#f59e0b",
        "HIGH": "#ea580c",
        "CRITICAL": "#ef4444",
    }
    colors = [color_map.get(label, "#94a3b8") for label in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=colors),
                textinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title="Protocol Deviation Severity (Synthetic Demo Data)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=340,
    )
    return fig


def plot_site_risk_heatmap(risks: List[SiteRisk]) -> go.Figure:
    """Heatmap showing 6 risk dimensions for each candidate site."""
    if not risks:
        fig = go.Figure()
        fig.add_annotation(text="No site risk data available", showarrow=False)
        fig.update_layout(title="Site Multi-Dimensional Risk Heatmap", height=380)
        return fig

    site_names = [r.site_name[:20] for r in risks[:10]]
    dimensions = [
        "Recruitment Risk",
        "Compliance Risk",
        "Data Quality Risk",
        "Operational Risk",
        "Capacity Risk",
        "Activation Risk",
    ]

    z_matrix = []
    for r in risks[:10]:
        z_matrix.append([
            r.recruitment_risk,
            r.compliance_risk,
            r.data_quality_risk,
            r.operational_risk,
            r.capacity_risk,
            r.activation_risk,
        ])

    fig = go.Figure(
        data=go.Heatmap(
            z=z_matrix,
            x=dimensions,
            y=site_names,
            colorscale="RdYlGn_r",  # Green low risk, Red high risk
            zmin=0,
            zmax=100,
            colorbar=dict(title="Risk (0-100)"),
        )
    )
    fig.update_layout(
        title="Site Multi-Dimensional Risk Heatmap (Synthetic Demo Data)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
    )
    return fig


def plot_site_radar(perf: SitePerformance) -> go.Figure:
    """Radar chart displaying individual site performance dimensions."""
    categories = [
        "Enrollment Velocity",
        "Experience",
        "Compliance",
        "Data Quality",
        "Operations",
        "Capacity",
    ]
    values = [
        perf.enrollment_velocity_score,
        perf.experience_score,
        perf.compliance_score,
        perf.data_quality_score,
        perf.operational_efficiency_score,
        perf.capacity_score,
    ]
    # Close the radar loop
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure(
        data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(16, 185, 129, 0.25)",
            line=dict(color="#10b981", width=2),
            name=perf.site_name,
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title=f"Performance Profile: {perf.site_name[:24]} (Synthetic)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig
