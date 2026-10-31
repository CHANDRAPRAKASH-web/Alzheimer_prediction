"""
=========================================================
Aid Axis - Cognitive Health Overview

Presents high-level summary cards, recent status, and
actionable starting points. Includes honest empty states
when no assessment records exist.
=========================================================
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List

from app.cognitive.styles import render_metric_card
from services.analytics_service import compute_aggregate_overview, parse_iso_date
from database.repository import AssessmentRepository


def render_cognitive_overview(
    patient_id: str,
    repository: AssessmentRepository,
    on_start_assessment=None
):
    """
    Renders the Cognitive Health Engine Overview dashboard.
    """
    st.markdown("## 📋 Cognitive Health Overview")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -0.5rem;'>"
        "Assess, record, and monitor cognitive performance over time."
        "</p>",
        unsafe_allow_html=True
    )

    # Fetch real records from repository
    assessments = repository.get_assessments_by_patient(patient_id, order_asc=True)
    overview_data = compute_aggregate_overview(assessments)

    if not overview_data["has_data"]:
        # Empty State
        st.markdown(
            """
            <div class="aidaxis-card aidaxis-card-accent" style="text-align: center; padding: 3rem 1.5rem; margin-top: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📋</div>
                <h3 style="color: #F8FAFC; margin-bottom: 0.5rem;">No assessments recorded yet</h3>
                <p style="color: #94A3B8; max-width: 520px; margin: 0 auto 1.75rem auto; font-size: 0.95rem; line-height: 1.5;">
                    Establishing a cognitive baseline enables structured tracking across orientation, 
                    memory registration, concentration, language, and executive domains.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_space1, col_btn, col_space2 = st.columns([1, 2, 1])
        with col_btn:
            if st.button("🚀 Start Cognitive Assessment", type="primary", use_container_width=True):
                if on_start_assessment:
                    on_start_assessment()
                else:
                    st.session_state["cognitive_subpage"] = "New Assessment"
                    st.rerun()

        st.markdown(
            """
            <div class="aidaxis-notice" style="margin-top: 2rem;">
                <strong>Clinical Scope:</strong> The assessment module utilizes the 
                <em>Cognitive Monitoring Questionnaire — Prototype (v1.0)</em> for research 
                and observational tracking. It does not replace a comprehensive neuropsychological exam.
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Data is present - Render Metrics Cards
    count = overview_data["count"]
    latest_score = overview_data["latest_score"]
    latest_date_str = overview_data["latest_date"]
    prev_score = overview_data["prev_score"]
    score_change = overview_data["score_change"]
    domains_count = overview_data["domains_assessed"]

    # Format date
    dt_latest = parse_iso_date(latest_date_str)
    formatted_date = dt_latest.strftime("%b %d, %Y") if dt_latest else "Recorded"

    # Row 1: Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card(
            title="Latest Assessment Score",
            value=f"{latest_score:.0f} / 30",
            subtitle=f"Recorded on {formatted_date}",
            accent_type="violet"
        )

    with col2:
        if prev_score is not None:
            sign = "+" if score_change > 0 else ("" if score_change == 0 else "-")
            color_accent = "teal" if score_change >= 0 else "amber"
            render_metric_card(
                title="Change from Previous",
                value=f"{sign}{score_change:.1f} pts",
                subtitle=f"Prior score: {prev_score:.0f} / 30",
                accent_type=color_accent
            )
        else:
            render_metric_card(
                title="Change from Previous",
                value="N/A",
                subtitle="Baseline assessment recorded",
                accent_type="violet"
            )

    with col3:
        render_metric_card(
            title="Completed Assessments",
            value=f"{count}",
            subtitle=f"{domains_count} cognitive domains evaluated",
            accent_type="teal"
        )

    # Quick summary of the latest record
    latest_record = assessments[-1]
    st.markdown("### 📊 Latest Assessment Breakdown")
    domain_scores = latest_record.get("domain_scores", {})
    
    if domain_scores:
        cols = st.columns(min(len(domain_scores), 4))
        for idx, (dom_id, dom_info) in enumerate(domain_scores.items()):
            col = cols[idx % 4]
            with col:
                score = dom_info.get("score", 0.0)
                max_s = dom_info.get("max_score", 1.0)
                pct = (score / max_s * 100.0) if max_s > 0 else 0
                st.markdown(
                    f"""
                    <div class="aidaxis-card" style="padding: 0.9rem 1rem; margin-bottom: 0.75rem;">
                        <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase;">{dom_info.get('title', dom_id)}</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 0.2rem 0;">
                            {score:.0f} <span style="font-size: 0.85rem; color: #64748B;">/ {max_s:.0f}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #A78BFA;">{pct:.0f}% achieved</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Call to action
    col_act1, col_act2 = st.columns([2, 1])
    with col_act1:
        st.markdown(
            f"<div style='color: #94A3B8; padding-top: 0.6rem;'>"
            f"Active Patient Profile: <strong>{patient_id}</strong> &nbsp;|&nbsp; "
            f"Last update: {formatted_date}"
            f"</div>",
            unsafe_allow_html=True
        )
    with col_act2:
        if st.button("➕ Conduct New Assessment", type="primary", use_container_width=True):
            if on_start_assessment:
                on_start_assessment()
            else:
                st.session_state["cognitive_subpage"] = "New Assessment"
                st.rerun()

    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Clinical Safety Disclaimer:</strong> This overview reflects structured self-reported 
            and caregiver-assisted performance logs. Scores can be influenced by diurnal variation, stress, 
            fatigue, and acute illnesses. This instrument does not replace diagnostic medical evaluations.
        </div>
        """,
        unsafe_allow_html=True
    )
