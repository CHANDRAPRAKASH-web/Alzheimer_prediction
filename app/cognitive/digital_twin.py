"""
=========================================================
Aid Axis - Cognitive Digital Twin (Prototype)

"A longitudinal summary of recorded cognitive assessment information."

CLINICAL & ARCHITECTURAL PRINCIPLES:
1. Honest, evidence-grounded representation of recorded data.
2. NOT a biological simulation, validated predictive model,
   or medical diagnostic system.
3. No fabricated future trajectories or arbitrary simulations.
4. Highlights recorded domain milestones and missing data.
=========================================================
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List

from database.repository import AssessmentRepository
from services.analytics_service import parse_iso_date


def render_cognitive_digital_twin(
    patient_id: str,
    repository: AssessmentRepository
):
    """
    Renders the Cognitive Digital Twin prototype.
    """
    st.markdown("## 🧬 Cognitive Digital Twin — Prototype")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -0.5rem;'>"
        "A longitudinal summary of recorded cognitive assessment information."
        "</p>",
        unsafe_allow_html=True
    )

    # Prominent Boundary & Disclaimer Alert
    st.markdown(
        """
        <div class="aidaxis-notice" style="border-left-color: #A78BFA;">
            <strong>Prototype Boundary Notice:</strong> This Cognitive Digital Twin is a structured 
            longitudinal profile synthesizing recorded assessment scores over time. 
            It is <strong>not</strong> a biological simulation, a predictive disease model, 
            or a diagnostic device. It reflects only documented test performance.
        </div>
        """,
        unsafe_allow_html=True
    )

    assessments = repository.get_assessments_by_patient(patient_id, order_asc=True)
    count = len(assessments)

    if count == 0:
        st.markdown(
            """
            <div class="aidaxis-card" style="text-align: center; padding: 3rem 1.5rem; margin-top: 1rem;">
                <div style="font-size: 2.75rem; margin-bottom: 0.75rem;">👤</div>
                <h4 style="color: #F8FAFC;">Cognitive Profile Uninitialized</h4>
                <p style="color: #94A3B8; max-width: 460px; margin: 0 auto 1.5rem auto; font-size: 0.95rem;">
                    No assessment records exist for this patient profile. Complete a structured assessment 
                    to establish your longitudinal cognitive twin.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Initialize Baseline Assessment", type="primary"):
            st.session_state["cognitive_subpage"] = "New Assessment"
            st.rerun()
        return

    latest = assessments[-1]
    dt_latest = parse_iso_date(latest.get("assessment_date", ""))
    date_str_latest = dt_latest.strftime("%B %d, %Y") if dt_latest else "Recorded"

    # Multi-card Twin Status Header
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="aidaxis-card aidaxis-card-accent">
                <div class="aidaxis-stat-label">Active Twin Profile</div>
                <div class="aidaxis-stat-val" style="font-size: 1.5rem;">{patient_id}</div>
                <div class="aidaxis-stat-sub">Updated {date_str_latest}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">Current Index Score</div>
                <div class="aidaxis-stat-val">{latest.get('total_score', 0):.1f} <span style="font-size: 1rem; color: #64748B;">/ {latest.get('max_score', 30):.0f}</span></div>
                <div class="aidaxis-stat-sub">{latest.get('percentage_score', 0):.1f}% Overall Performance</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="aidaxis-card aidaxis-card-teal">
                <div class="aidaxis-stat-label">Recorded History Depth</div>
                <div class="aidaxis-stat-val">{count}</div>
                <div class="aidaxis-stat-sub">Completed Milestones</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if count == 1:
        st.markdown(
            """
            <div class="aidaxis-card" style="margin-top: 1rem;">
                <p style="color: #CBD5E1; font-size: 0.95rem; margin: 0;">
                    <em>"Your cognitive profile will become more informative as additional comparable assessments are recorded."</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Domain Multi-Axis Radar Representation
    st.markdown("### 🕸️ Multi-Domain Performance Signature")
    st.write(
        "Visualizing performance across validated cognitive dimensions based strictly on recorded tests:"
    )

    domains = latest.get("domain_scores", {})
    if domains:
        labels = [d.get("title", k) for k, d in domains.items()]
        pcts = [d.get("percentage", 0.0) for d in domains.values()]

        fig = go.Figure()

        # Add Latest
        fig.add_trace(go.Scatterpolar(
            r=pcts + [pcts[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=f"Latest ({date_str_latest})",
            line=dict(color="#A78BFA", width=2.5),
            fillcolor="rgba(167, 139, 250, 0.25)"
        ))

        # Add Previous if exists
        if count >= 2:
            prev = assessments[-2]
            dt_prev = parse_iso_date(prev.get("assessment_date", ""))
            d_prev_str = dt_prev.strftime("%b %d, %Y") if dt_prev else "Previous"
            prev_domains = prev.get("domain_scores", {})
            prev_pcts = [prev_domains.get(k, {}).get("percentage", 0.0) for k in domains.keys()]
            fig.add_trace(go.Scatterpolar(
                r=prev_pcts + [prev_pcts[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name=f"Previous ({d_prev_str})",
                line=dict(color="#64748B", width=1.5, dash="dash"),
                fillcolor="rgba(100, 116, 139, 0.1)"
            ))

        fig.update_layout(
            polar=dict(
                bgcolor="#151E2E",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#233148", color="#94A3B8"),
                angularaxis=dict(gridcolor="#233148", color="#F1F5F9")
            ),
            paper_bgcolor="#151E2E",
            font=dict(color="#94A3B8"),
            height=420,
            margin=dict(l=50, r=50, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Domain Inventory Table
    st.markdown("### 📋 Recorded Domain Scores (Latest Session)")
    cols = st.columns(min(len(domains), 4))
    for idx, (dom_id, dom_data) in enumerate(domains.items()):
        col = cols[idx % 4]
        with col:
            s = dom_data.get("score", 0.0)
            m = dom_data.get("max_score", 1.0)
            pct = dom_data.get("percentage", 0.0)
            st.markdown(
                f"""
                <div class="aidaxis-card" style="padding: 0.85rem 1rem; margin-bottom: 0.75rem;">
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">{dom_data.get('title', dom_id)}</div>
                    <div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC;">
                        {s:.1f} <span style="font-size: 0.85rem; color: #64748B;">/ {m:.0f}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: {'#14B8A6' if pct >= 80 else ('#F59E0B' if pct >= 50 else '#EF4444')};">
                        {pct:.0f}% Achieved
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Longitudinal Timeline Profile
    st.markdown("### ⏳ Longitudinal Timeline Profile")
    st.write("Chronological sequence of recorded assessment milestones:")

    for i, a in enumerate(assessments[::-1]):
        dt = parse_iso_date(a.get("assessment_date", ""))
        d_str = dt.strftime("%B %d, %Y at %H:%M UTC") if dt else a.get("assessment_date", "")[:10]
        s = a.get("total_score", 0.0)
        m = a.get("max_score", 30.0)
        pct = a.get("percentage_score", 0.0)
        rec_id = a.get("assessment_id")

        st.markdown(
            f"""
            <div class="aidaxis-card" style="border-left: 4px solid {'#14B8A6' if i == 0 else '#475569'}; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div>
                        <span class="aidaxis-badge {'aidaxis-badge-teal' if i == 0 else 'aidaxis-badge-violet'}">
                            {'Latest Milestone' if i == 0 else f'Milestone #{count - i}'}
                        </span>
                        <h4 style="margin: 0.35rem 0 0.1rem 0; color: #F8FAFC;">{d_str}</h4>
                        <div style="font-size: 0.8rem; color: #94A3B8;">ID: {rec_id} &nbsp;|&nbsp; {a.get('assessment_type')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.4rem; font-weight: 700; color: #F8FAFC;">{s:.1f} / {m:.0f}</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">{pct:.1f}% Score</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Scientific Boundary:</strong> This twin reflects historical and observational assessment records. 
            No simulated futures, projected trajectories, or synthetic biomarkers are generated.
        </div>
        """,
        unsafe_allow_html=True
    )
