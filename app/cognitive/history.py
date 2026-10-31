"""
=========================================================
Aid Axis - Assessment History

Renders a chronological assessment history table with
score comparisons, search/filter, and detailed modal/expander
inspections for domain breakdown, recorded responses, and notes.
=========================================================
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from database.repository import AssessmentRepository
from services.analytics_service import parse_iso_date


def render_assessment_history(
    patient_id: str,
    repository: AssessmentRepository
):
    """
    Renders chronological assessment history table and detail inspector.
    """
    st.markdown("## 📜 Assessment History")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 0.95rem; margin-top: -0.5rem;'>"
        "Chronological ledger of completed cognitive assessments and domain breakdowns."
        "</p>",
        unsafe_allow_html=True
    )

    # Fetch records
    assessments = repository.get_assessments_by_patient(patient_id, order_asc=True)

    if not assessments:
        st.markdown(
            """
            <div class="aidaxis-card" style="text-align: center; padding: 2.5rem 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📭</div>
                <h4 style="color: #F8FAFC;">No assessment history recorded</h4>
                <p style="color: #94A3B8; max-width: 420px; margin: 0 auto 1.25rem auto; font-size: 0.9rem;">
                    Completed assessments for this profile will be preserved and cataloged here.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Conduct First Assessment", type="primary"):
            st.session_state["cognitive_subpage"] = "New Assessment"
            st.rerun()
        return

    # Build display table data with consecutive changes
    table_rows = []
    for i, rec in enumerate(assessments):
        dt = parse_iso_date(rec.get("assessment_date", ""))
        date_str = dt.strftime("%Y-%m-%d %H:%M") if dt else rec.get("assessment_date", "")[:16]
        
        score = float(rec.get("total_score", 0.0))
        max_s = float(rec.get("max_score", 30.0))
        
        # Calculate change from previous
        if i == 0:
            change_str = "Baseline"
        else:
            prev_s = float(assessments[i-1].get("total_score", 0.0))
            diff = score - prev_s
            sign = "+" if diff > 0 else ""
            change_str = f"{sign}{diff:.1f} pts"

        table_rows.append({
            "Record ID": rec.get("assessment_id"),
            "Date & Time (UTC)": date_str,
            "Instrument": rec.get("assessment_type"),
            "Score": f"{score:.1f}",
            "Max": f"{max_s:.0f}",
            "Score %": f"{rec.get('percentage_score', 0):.1f}%",
            "Change": change_str
        })

    # Render table (show most recent first in table display)
    df_display = pd.DataFrame(table_rows[::-1])
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # Detail Inspector
    st.markdown("### 🔍 Inspect Assessment Record Details")
    
    # Selection dropdown
    record_options = {
        f"{r['assessment_id']} ({r['assessment_date'][:10]} - Score: {r['total_score']:.1f}/{r['max_score']:.0f})": r['assessment_id']
        for r in assessments[::-1]
    }
    
    selected_label = st.selectbox(
        "Select an assessment record to inspect:",
        list(record_options.keys())
    )
    
    if selected_label:
        selected_id = record_options[selected_label]
        target_rec = repository.get_assessment_by_id(selected_id)
        if target_rec:
            render_record_details(target_rec)


def render_record_details(rec: Dict[str, Any]):
    """
    Renders structured details of an individual assessment.
    """
    aid = rec.get("assessment_id")
    dt = parse_iso_date(rec.get("assessment_date", ""))
    date_formatted = dt.strftime("%B %d, %Y at %H:%M UTC") if dt else rec.get("assessment_date")
    total = rec.get("total_score", 0.0)
    max_s = rec.get("max_score", 30.0)
    pct = rec.get("percentage_score", 0.0)

    st.markdown(
        f"""
        <div class="aidaxis-card aidaxis-card-accent">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="aidaxis-badge aidaxis-badge-violet">{rec.get('assessment_type')}</span>
                    <h3 style="margin: 0.4rem 0 0.2rem 0; color: #F8FAFC;">Record: {aid}</h3>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Recorded on {date_formatted} &nbsp;|&nbsp; Version: {rec.get('assessment_version')}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #F8FAFC;">{total:.1f} / {max_s:.0f}</div>
                    <div style="font-size: 0.85rem; color: #14B8A6; font-weight: 600;">{pct:.1f}% Score</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Domain Scores
    st.markdown("#### Domain Scores Breakdown:")
    domains = rec.get("domain_scores", {})
    if domains:
        d_cols = st.columns(min(len(domains), 4))
        for idx, (dom_id, dom_data) in enumerate(domains.items()):
            col = d_cols[idx % 4]
            with col:
                s = dom_data.get("score", 0.0)
                m = dom_data.get("max_score", 1.0)
                p = dom_data.get("percentage", 0.0)
                st.markdown(
                    f"""
                    <div class="aidaxis-card" style="padding: 0.75rem 0.9rem; margin-bottom: 0.5rem;">
                        <div style="font-size: 0.75rem; color: #94A3B8;">{dom_data.get('title', dom_id)}</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">{s:.1f} / {m:.0f}</div>
                        <div style="font-size: 0.75rem; color: #A78BFA;">{p:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Notes
    notes = rec.get("notes", "")
    if notes:
        st.markdown("#### Examiner Notes:")
        st.info(notes)

    # Raw responses in expander
    with st.expander("🔎 View Recorded Response Data"):
        st.json(rec.get("responses", {}))
