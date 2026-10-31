"""
=========================================================
Aid Axis - Cognitive Progress Dashboard

Provides interactive longitudinal charts:
- Line chart of total assessment scores over time
- Consecutive assessment comparative delta view
- Domain-level performance radar and bar charts
- Strictly relies on actual saved database records
- Non-fabricated, honest empty states for <2 records
=========================================================
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List

from database.repository import AssessmentRepository
from services.analytics_service import (
    parse_iso_date,
    compare_consecutive_assessments
)


def render_progress_dashboard(
    patient_id: str,
    repository: AssessmentRepository
):
    """
    Renders the Cognitive Progress Dashboard with longitudinal analytics.
    """
    st.markdown("## 📈 Cognitive Progress Dashboard")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 0.95rem; margin-top: -0.5rem;'>"
        "Longitudinal visualization of cognitive assessment trajectory and domain performance."
        "</p>",
        unsafe_allow_html=True
    )

    # Fetch chronological records
    assessments = repository.get_assessments_by_patient(patient_id, order_asc=True)

    if not assessments:
        st.markdown(
            """
            <div class="aidaxis-card" style="text-align: center; padding: 3rem 1.5rem;">
                <div style="font-size: 2.75rem; margin-bottom: 0.75rem;">📊</div>
                <h4 style="color: #F8FAFC;">No assessment records found</h4>
                <p style="color: #94A3B8; max-width: 450px; margin: 0 auto 1.5rem auto; font-size: 0.95rem;">
                    Score trajectories and domain analytics require saved assessment entries.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Start First Assessment", type="primary"):
            st.session_state["cognitive_subpage"] = "New Assessment"
            st.rerun()
        return

    # Check for minimum comparable assessments
    if len(assessments) < 2:
        st.markdown(
            """
            <div class="aidaxis-card aidaxis-card-accent" style="padding: 2rem 1.5rem; margin-top: 1rem;">
                <h4 style="color: #F8FAFC; margin-bottom: 0.5rem;">Baseline Established (1 Recorded Assessment)</h4>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.5;">
                    Complete at least two comparable assessments to view score changes over time and track longitudinal trajectories.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Render single assessment radar snapshot
        render_single_assessment_snapshot(assessments[0])
        return

    # Multi-assessment available: Render longitudinal line chart
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 1rem; margin-bottom: 0.5rem;">
            <h4 style="margin: 0; color: #F8FAFC;">Assessment Score Trajectory Over Time</h4>
            <span style="font-size: 0.8rem; color: #94A3B8;">Instrument: Cognitive Monitoring Questionnaire (Scale: 0–30)</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    dates = []
    scores = []
    hover_texts = []
    for rec in assessments:
        dt = parse_iso_date(rec.get("assessment_date", ""))
        d_str = dt.strftime("%Y-%m-%d %H:%M") if dt else rec.get("assessment_date", "")[:10]
        dates.append(d_str)
        s = float(rec.get("total_score", 0.0))
        scores.append(s)
        hover_texts.append(
            f"<b>{d_str}</b><br>"
            f"Score: {s:.1f} / {rec.get('max_score', 30.0):.0f}<br>"
            f"Percentage: {rec.get('percentage_score', 0):.1f}%"
        )

    # Plotly Line Chart with refined healthcare styling
    fig_line = go.Figure()

    fig_line.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode="lines+markers",
        name="Recorded Score",
        line=dict(color="#A78BFA", width=3, shape="spline"),
        marker=dict(size=9, color="#7C3AED", line=dict(color="#F8FAFC", width=2)),
        hoverinfo="text",
        text=hover_texts
    ))

    # Reference ceiling line
    fig_line.add_trace(go.Scatter(
        x=dates,
        y=[30.0] * len(dates),
        mode="lines",
        name="Maximum Score (30)",
        line=dict(color="#334155", width=1.5, dash="dash"),
        hoverinfo="skip"
    ))

    fig_line.update_layout(
        paper_bgcolor="#151E2E",
        plot_bgcolor="#151E2E",
        font=dict(color="#94A3B8", family="Plus Jakarta Sans, sans-serif"),
        margin=dict(l=40, r=40, t=30, b=40),
        xaxis=dict(
            gridcolor="#233148",
            showgrid=True,
            title="Assessment Date"
        ),
        yaxis=dict(
            gridcolor="#233148",
            showgrid=True,
            range=[0, 32],
            title="Total Score (Points)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=380
    )

    st.plotly_chart(fig_line, use_container_width=True)

    # Consecutive Comparison Section
    latest_rec = assessments[-1]
    prev_rec = assessments[-2]
    comp = compare_consecutive_assessments(latest_rec, prev_rec)

    st.markdown("### 🔄 Consecutive Assessment Comparison")
    diff = comp["score_diff"]
    sign = "+" if diff > 0 else ""
    card_accent = "teal" if diff >= 0 else "amber"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="aidaxis-card {f'aidaxis-card-{card_accent}'}">
                <div class="aidaxis-stat-label">Consecutive Shift</div>
                <div class="aidaxis-stat-val">{sign}{diff:.1f} pts</div>
                <div class="aidaxis-stat-sub">From {comp['previous_score']:.1f} to {comp['latest_score']:.1f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        days = comp.get("days_elapsed")
        days_str = f"{days} days" if days is not None else "N/A"
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">Interval Elapsed</div>
                <div class="aidaxis-stat-val">{days_str}</div>
                <div class="aidaxis-stat-sub">Between consecutive tests</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        status_text = "Stable" if diff == 0 else ("Higher" if diff > 0 else "Lower")
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">Short-Term Dynamic</div>
                <div class="aidaxis-stat-val" style="font-size: 1.5rem;">{status_text}</div>
                <div class="aidaxis-stat-sub">Descriptive comparison only</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Domain Performance Comparison Bar Chart
    st.markdown("### 📊 Domain Performance Shift")
    st.write("Comparison of domain sub-scores between the last two assessments:")

    domain_deltas = comp.get("domain_deltas", {})
    if domain_deltas:
        dom_names = [d["title"] for d in domain_deltas.values()]
        curr_scores = [d["current_score"] for d in domain_deltas.values()]
        old_scores = [d["previous_score"] for d in domain_deltas.values()]

        fig_bar = go.Figure(data=[
            go.Bar(
                name="Previous Assessment",
                x=dom_names,
                y=old_scores,
                marker_color="#475569"
            ),
            go.Bar(
                name="Latest Assessment",
                x=dom_names,
                y=curr_scores,
                marker_color="#14B8A6"
            )
        ])

        fig_bar.update_layout(
            barmode="group",
            paper_bgcolor="#151E2E",
            plot_bgcolor="#151E2E",
            font=dict(color="#94A3B8"),
            margin=dict(l=30, r=30, t=30, b=40),
            xaxis=dict(gridcolor="#233148"),
            yaxis=dict(gridcolor="#233148", title="Score"),
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Clinical Safety Note:</strong> Minor score shifts do not represent definitive 
            cognitive deterioration or improvement. Longitudinal evaluation across multiple time points 
            and clinical correlation are required.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_single_assessment_snapshot(rec: Dict[str, Any]):
    """
    Renders baseline domain overview when only one assessment is saved.
    """
    st.markdown("#### Baseline Domain Scores:")
    domains = rec.get("domain_scores", {})
    if domains:
        names = [d.get("title", k) for k, d in domains.items()]
        pcts = [d.get("percentage", 0.0) for d in domains.values()]

        # Radar chart for baseline
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=pcts + [pcts[0]],
            theta=names + [names[0]],
            fill="toself",
            name="Baseline %",
            line=dict(color="#A78BFA", width=2),
            fillcolor="rgba(167, 139, 250, 0.2)"
        ))

        fig_radar.update_layout(
            polar=dict(
                bgcolor="#151E2E",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#233148", color="#94A3B8"),
                angularaxis=dict(gridcolor="#233148", color="#E2E8F0")
            ),
            paper_bgcolor="#151E2E",
            font=dict(color="#94A3B8"),
            height=360,
            margin=dict(l=40, r=40, t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
