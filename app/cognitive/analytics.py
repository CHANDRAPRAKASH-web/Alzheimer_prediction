"""
=========================================================
Aid Axis - Cognitive Progression Analytics

Provides descriptive analytics, domain variance analysis,
and clinically responsible narrative interpretations.
Strictly avoids predictive or diagnostic disease claims.
=========================================================
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from database.repository import AssessmentRepository
from services.analytics_service import (
    compare_consecutive_assessments,
    generate_progression_narrative,
    parse_iso_date
)


def render_progression_analytics(
    patient_id: str,
    repository: AssessmentRepository
):
    """
    Renders Progression Analytics view with cautious, evidence-grounded insights.
    """
    st.markdown("## 🔬 Progression Analytics")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 0.95rem; margin-top: -0.5rem;'>"
        "Objective statistical analysis of recorded score changes and domain-level variance."
        "</p>",
        unsafe_allow_html=True
    )

    assessments = repository.get_assessments_by_patient(patient_id, order_asc=True)
    count = len(assessments)

    if count == 0:
        st.markdown(
            """
            <div class="aidaxis-card" style="text-align: center; padding: 2.5rem 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
                <h4 style="color: #F8FAFC;">No assessment records available</h4>
                <p style="color: #94A3B8; max-width: 450px; margin: 0 auto 1.25rem auto;">
                    Progression analytics requires at least one baseline assessment.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # If 1 assessment
    if count == 1:
        rec = assessments[0]
        dt = parse_iso_date(rec.get("assessment_date", ""))
        d_str = dt.strftime("%B %d, %Y") if dt else rec.get("assessment_date", "")[:10]
        st.markdown(
            f"""
            <div class="aidaxis-card aidaxis-card-accent" style="padding: 1.5rem;">
                <h4 style="color: #F8FAFC; margin-bottom: 0.4rem;">Baseline Assessment Cataloged</h4>
                <div style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                    • Recorded Score: <strong>{rec.get('total_score', 0):.1f} / {rec.get('max_score', 30):.0f}</strong> ({rec.get('percentage_score', 0):.1f}%)<br/>
                    • Date Established: <strong>{d_str}</strong><br/>
                    • Assessment Type: <strong>{rec.get('assessment_type')}</strong>
                </div>
                <p style="color: #CBD5E1; margin-top: 1rem; font-size: 0.9rem;">
                    <em>Additional assessments are needed to establish a meaningful trend and evaluate longitudinal variation.</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # 2 or more assessments: Comparative Analytics
    latest = assessments[-1]
    prev = assessments[-2]
    comp = compare_consecutive_assessments(latest, prev)

    dt_latest = parse_iso_date(latest.get("assessment_date", ""))
    dt_prev = parse_iso_date(prev.get("assessment_date", ""))
    str_latest = dt_latest.strftime("%b %d, %Y") if dt_latest else "Latest"
    str_prev = dt_prev.strftime("%b %d, %Y") if dt_prev else "Previous"

    # Key Comparative Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="aidaxis-card aidaxis-card-violet">
                <div class="aidaxis-stat-label">Latest Score</div>
                <div class="aidaxis-stat-val">{comp['latest_score']:.1f}</div>
                <div class="aidaxis-stat-sub">{str_latest}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">Previous Score</div>
                <div class="aidaxis-stat-val">{comp['previous_score']:.1f}</div>
                <div class="aidaxis-stat-sub">{str_prev}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        diff = comp["score_diff"]
        sign = "+" if diff > 0 else ""
        c_type = "teal" if diff >= 0 else "amber"
        st.markdown(
            f"""
            <div class="aidaxis-card aidaxis-card-{c_type}">
                <div class="aidaxis-stat-label">Absolute Score Change</div>
                <div class="aidaxis-stat-val">{sign}{diff:.1f} pts</div>
                <div class="aidaxis-stat-sub">Delta = |{comp['abs_score_diff']:.1f}|</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">Total Time-Series Records</div>
                <div class="aidaxis-stat-val">{count}</div>
                <div class="aidaxis-stat-sub">Historical evaluations</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Narrative Interpretation
    st.markdown("### 📝 Objective Trend Summary")
    narrative = generate_progression_narrative(comp, count)
    st.markdown(
        f"""
        <div class="aidaxis-card" style="border-left: 4px solid #8B5CF6; line-height: 1.6; font-size: 0.95rem; color: #E2E8F0;">
            {narrative}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Domain Shift Table
    st.markdown("### 🔍 Domain-Level Variance Analysis")
    st.write("Detailed examination of individual cognitive domain shifts between the two most recent records:")

    domain_deltas = comp.get("domain_deltas", {})
    if domain_deltas:
        d_rows = []
        for dom_id, d_info in domain_deltas.items():
            delta = d_info["delta"]
            sign = "+" if delta > 0 else ""
            status_badge = "🟩 Higher" if delta > 0 else ("🟧 Lower" if delta < 0 else "⬜ Stable")
            d_rows.append({
                "Cognitive Domain": d_info["title"],
                "Previous Score": f"{d_info['previous_score']:.1f} / {d_info['max_score']:.0f}",
                "Latest Score": f"{d_info['current_score']:.1f} / {d_info['max_score']:.0f}",
                "Delta (pts)": f"{sign}{delta:.1f}",
                "Recorded Shift": status_badge
            })

        df_domains = pd.DataFrame(d_rows)
        st.dataframe(df_domains, use_container_width=True, hide_index=True)

    # Clinical Safety & Confounding Factors Advisory
    st.markdown(
        """
        <div class="aidaxis-notice" style="margin-top: 1.5rem;">
            <h4 style="margin-top: 0; color: #F8FAFC;">⚠️ Confounding Factors Advisory</h4>
            <p style="margin-bottom: 0.5rem; font-size: 0.9rem;">
                Cognitive test scores can fluctuate substantially based on external and systemic factors, including:
            </p>
            <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.85rem; color: #CBD5E1; line-height: 1.6;">
                <li>Sleep fragmentation, insomnia, or circadian disruptions</li>
                <li>Acute psychological stress, anxiety, or depressive symptoms</li>
                <li>Systemic illness, dehydration, infections (e.g., UTI), or metabolic shifts</li>
                <li>Pharmacotherapy alterations, sedatives, or anticholinergic medications</li>
                <li>Environmental distractions or lack of testing standardization</li>
            </ul>
            <p style="margin-top: 0.75rem; font-size: 0.85rem; color: #A78BFA;">
                <strong>Recommendation:</strong> A questionnaire score alone must not be used to diagnose Alzheimer's 
                disease or predict the future course of the disease. Any persistent or concerning cognitive decline 
                should prompt comprehensive clinical evaluation by a qualified neurologist or geriatrician.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
