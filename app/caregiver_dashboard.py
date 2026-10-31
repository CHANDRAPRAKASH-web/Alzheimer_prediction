"""
=========================================================
Aid Axis - Caregiver Dashboard

Enables authorised caregivers to:
  A. Patient Overview        — summary cards for assigned patients
  B. Cognitive Progress      — real assessment history charts
  C. Patient Record Mgmt     — read-only access to patient documents
     (same records as Medical Document Vault; no separate upload)

Uses real data from AssessmentRepository + DocumentRepository.
Never fabricates assessment scores or clinical conclusions.

IMPORTANT: All dynamic HTML is built via string concatenation,
NOT triple-quoted f-strings with indented interpolated variables,
to avoid Streamlit's 4-space CommonMark code-block rule.
=========================================================
"""

import html as _html
import base64
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional

from database.repository import AssessmentRepository
from database.document_repository import DocumentRepository, DOCUMENT_CATEGORIES
from services.analytics_service import compute_aggregate_overview, parse_iso_date

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


# ---------------------------------------------------------------------------
# Patient profiles for demo (matched to seeded assessment data)
# ---------------------------------------------------------------------------
_PATIENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "PATIENT-001": {
        "name": "Primary User",
        "age": None,
        "dob": None,
        "care_notes": "Self-managed profile. No caregiver-assigned notes.",
        "assigned_clinician": "—",
    },
    "PATIENT-002": {
        "name": "Arthur Pendelton",
        "age": 76,
        "dob": "1948-03-12",
        "care_notes": (
            "Lives with spouse. Attends weekly memory clinic. "
            "Prefers morning assessments. Mild hesitation on attention tasks noted."
        ),
        "assigned_clinician": "Dr. Sarah Lin, MD",
    },
    "PATIENT-003": {
        "name": "Margaret Chen",
        "age": 68,
        "dob": "1956-07-24",
        "care_notes": (
            "Post-hospitalization monitoring. Sleep quality improving. "
            "Responsive to structured cognitive exercises."
        ),
        "assigned_clinician": "Dr. Robert Vance, MD",
    },
    "PATIENT-004": {
        "name": "Robert Thorne",
        "age": 81,
        "dob": "1943-11-05",
        "care_notes": (
            "Active community volunteer. High cognitive reserve. "
            "Quarterly healthy-aging cohort participant."
        ),
        "assigned_clinician": "Dr. Sarah Lin, MD",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(v) -> str:
    """HTML-escape a value for safe embedding in st.markdown HTML."""
    return _html.escape(str(v)) if v is not None else ""


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def _score_color(pct: float) -> str:
    if pct >= 85:
        return "#14B8A6"
    elif pct >= 65:
        return "#F59E0B"
    return "#EF4444"


def _category_icon(cat: str) -> str:
    icons = {
        "Medical Reports": "🏥",
        "Prescriptions": "💊",
        "Laboratory Reports": "🔬",
        "Clinical Summaries": "📋",
        "Other Documents": "📂",
    }
    return icons.get(cat, "📄")


def _mime_for_download(file_type: str, original_filename: str) -> str:
    ext = original_filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return "application/pdf"
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    return "application/octet-stream"


def _md(html: str):
    """Shorthand for st.markdown with unsafe_allow_html=True."""
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_caregiver_state():
    if "cg_selected_patient" not in st.session_state:
        st.session_state["cg_selected_patient"] = "PATIENT-002"
    if "cg_doc_preview_id" not in st.session_state:
        st.session_state["cg_doc_preview_id"] = None
    if "cg_doc_filter_cat" not in st.session_state:
        st.session_state["cg_doc_filter_cat"] = "All Categories"
    if "cg_doc_search" not in st.session_state:
        st.session_state["cg_doc_search"] = ""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_caregiver_dashboard(
    assessment_repo: AssessmentRepository,
    document_repo: DocumentRepository,
):
    """Main entry point for the Caregiver Dashboard."""
    _init_caregiver_state()

    st.markdown("## 👩‍⚕️ Caregiver Dashboard")
    _md(
        "<p style='color:#94A3B8;font-size:1.05rem;margin-top:-0.5rem;'>"
        "Review patient overviews, cognitive progress, and medical records."
        "</p>"
    )

    # ── Patient selector ──────────────────────────────────────────────
    all_patients_in_db = assessment_repo.get_all_patients()
    known = list(_PATIENT_PROFILES.keys())
    combined = sorted(set(all_patients_in_db + known))

    st.markdown("#### 🔍 Select Patient")
    pat_cols = st.columns(min(len(combined), 4))
    for i, pid in enumerate(combined):
        with pat_cols[i % 4]:
            profile = _PATIENT_PROFILES.get(pid, {})
            name = profile.get("name", pid)
            is_sel = st.session_state["cg_selected_patient"] == pid
            label = f"{'✅ ' if is_sel else ''}{name}\n({pid})"
            if st.button(
                label,
                key=f"cg_pat_btn_{pid}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state["cg_selected_patient"] = pid
                st.session_state["cg_doc_preview_id"] = None
                st.rerun()

    _md("<hr style='border-color:#233148;margin:1.25rem 0;'>")

    selected_pid = st.session_state["cg_selected_patient"]

    tab_overview, tab_cognitive, tab_records = st.tabs([
        "📋 Patient Overview",
        "📈 Cognitive Progress",
        "📁 Medical Records",
    ])

    with tab_overview:
        _render_patient_overview(selected_pid, assessment_repo, document_repo)
    with tab_cognitive:
        _render_cognitive_progress(selected_pid, assessment_repo)
    with tab_records:
        _render_patient_records(selected_pid, document_repo)


# ---------------------------------------------------------------------------
# A. Patient Overview — all HTML via concatenation (no triple-quote f-strings)
# ---------------------------------------------------------------------------

def _render_patient_overview(
    patient_id: str,
    assessment_repo: AssessmentRepository,
    document_repo: DocumentRepository,
):
    profile = _PATIENT_PROFILES.get(patient_id, {"name": patient_id})
    name = profile.get("name", patient_id)
    age = profile.get("age")
    dob = profile.get("dob")
    care_notes = profile.get("care_notes", "No care notes recorded.")
    clinician = profile.get("assigned_clinician", "—")

    assessments = assessment_repo.get_assessments_by_patient(patient_id, order_asc=True)
    overview = compute_aggregate_overview(assessments)
    doc_count = document_repo.count_documents(patient_id)

    age_str = f"Age {age}" if age else (f"DOB: {dob}" if dob else "Age: not recorded")
    assessment_badge = f'{overview["count"]} Assessment{"s" if overview["count"] != 1 else ""}'
    doc_badge = f'{doc_count} Document{"s" if doc_count != 1 else ""}'

    # ── Patient identity card ──
    _md(
        '<div class="aidaxis-card aidaxis-card-violet" style="padding:1.25rem 1.5rem;margin-bottom:1rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem;">'
        '<div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:#F8FAFC;">{_s(name)}</div>'
        f'<div style="font-size:0.9rem;color:#94A3B8;margin-top:0.2rem;">'
        f'Patient ID: <strong style="color:#C4B5FD;">{_s(patient_id)}</strong>'
        f'&nbsp;·&nbsp; {_s(age_str)}</div>'
        f'<div style="font-size:0.85rem;color:#64748B;margin-top:0.3rem;">'
        f'Assigned Clinician: {_s(clinician)}</div>'
        '</div>'
        '<div style="display:flex;gap:0.5rem;flex-wrap:wrap;">'
        f'<span class="aidaxis-badge aidaxis-badge-teal">{_s(assessment_badge)}</span>'
        f'<span class="aidaxis-badge aidaxis-badge-violet">{_s(doc_badge)}</span>'
        '</div>'
        '</div></div>'
    )

    # ── Summary metric cards ──
    col1, col2, col3 = st.columns(3)

    with col1:
        if overview["has_data"]:
            score = overview["latest_score"]
            pct = (score / 30 * 100) if score else 0
            clr = _score_color(pct)
            date_str = _fmt_ts(overview["latest_date"])
            _md(
                '<div class="aidaxis-card aidaxis-card-accent" style="padding:1rem 1.25rem;">'
                '<div class="aidaxis-stat-label">Latest Cognitive Score</div>'
                f'<div class="aidaxis-stat-val" style="color:{clr};">'
                f'{score:.0f}<span style="font-size:1rem;color:#64748B;"> / 30</span></div>'
                f'<div class="aidaxis-stat-sub">{_s(date_str)}</div>'
                '</div>'
            )
        else:
            _md(
                '<div class="aidaxis-card aidaxis-card-accent" style="padding:1rem 1.25rem;">'
                '<div class="aidaxis-stat-label">Latest Cognitive Score</div>'
                '<div class="aidaxis-stat-val" style="color:#475569;">—</div>'
                '<div class="aidaxis-stat-sub">No assessments recorded</div>'
                '</div>'
            )

    with col2:
        if overview["has_data"] and overview["score_change"] is not None:
            chg = overview["score_change"]
            sign = "+" if chg > 0 else ""
            chg_col = "#14B8A6" if chg >= 0 else "#EF4444"
            prev = overview["prev_score"]
            _md(
                '<div class="aidaxis-card aidaxis-card-teal" style="padding:1rem 1.25rem;">'
                '<div class="aidaxis-stat-label">Score Change</div>'
                f'<div class="aidaxis-stat-val" style="color:{chg_col};">{sign}{chg:.1f} pts</div>'
                f'<div class="aidaxis-stat-sub">vs. previous ({prev:.0f} / 30)</div>'
                '</div>'
            )
        else:
            _md(
                '<div class="aidaxis-card aidaxis-card-teal" style="padding:1rem 1.25rem;">'
                '<div class="aidaxis-stat-label">Score Change</div>'
                '<div class="aidaxis-stat-val" style="color:#475569;">—</div>'
                '<div class="aidaxis-stat-sub">Insufficient history</div>'
                '</div>'
            )

    with col3:
        _md(
            '<div class="aidaxis-card" style="padding:1rem 1.25rem;">'
            '<div class="aidaxis-stat-label">Medical Documents</div>'
            f'<div class="aidaxis-stat-val">{doc_count}</div>'
            '<div class="aidaxis-stat-sub">Stored in Medical Document Vault</div>'
            '</div>'
        )

    # ── Care notes ──
    st.markdown("#### 📝 Care Notes")
    _md(
        '<div class="aidaxis-card" style="padding:1rem 1.25rem;">'
        f'<div style="color:#CBD5E1;font-size:0.95rem;line-height:1.6;">{_s(care_notes)}</div>'
        '</div>'
    )

    # ── Recent assessment activity ──
    if assessments:
        st.markdown("#### 🕒 Recent Assessment Activity")
        for rec in reversed(assessments[-3:]):
            dt_str = _fmt_ts(rec["assessment_date"])
            score = rec["total_score"]
            pct = rec["percentage_score"]
            clr = _score_color(pct)
            notes_html = (
                f'<div style="font-size:0.8rem;color:#A78BFA;margin-top:0.1rem;">📝 {_s(rec["notes"])}</div>'
                if rec.get("notes") else ""
            )
            _md(
                '<div class="aidaxis-card" style="padding:0.85rem 1.1rem;margin-bottom:0.5rem;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<div>'
                f'<div style="font-size:0.95rem;font-weight:600;color:#F8FAFC;">Assessment on {_s(dt_str)}</div>'
                f'<div style="font-size:0.82rem;color:#94A3B8;">ID: {_s(rec["assessment_id"])}</div>'
                + notes_html +
                '</div>'
                '<div style="text-align:right;min-width:70px;">'
                f'<span style="font-size:1.1rem;font-weight:700;color:{clr};">{score:.0f}</span>'
                f'<span style="font-size:0.8rem;color:#64748B;">/30</span>'
                f'<div style="font-size:0.75rem;color:#64748B;">{pct:.1f}%</div>'
                '</div>'
                '</div></div>'
            )
    else:
        _md(
            '<div class="aidaxis-card" style="text-align:center;padding:1.5rem;">'
            '<div style="color:#64748B;font-size:0.95rem;">No assessment history available.</div>'
            '</div>'
        )

    _md(
        '<div class="aidaxis-disclaimer">'
        '<strong>Caregiver Notice:</strong> Assessment scores are observational records only. '
        'They do not constitute a clinical diagnosis of Alzheimer\'s disease or any other '
        'condition. Always consult a licensed clinician for medical evaluation.'
        '</div>'
    )


# ---------------------------------------------------------------------------
# B. Cognitive Progress — all HTML via concatenation
# ---------------------------------------------------------------------------

def _render_cognitive_progress(patient_id: str, assessment_repo: AssessmentRepository):
    profile = _PATIENT_PROFILES.get(patient_id, {})
    name = profile.get("name", patient_id)

    _md(
        '<div class="aidaxis-card aidaxis-card-teal" style="padding:1rem 1.25rem;margin-bottom:1rem;">'
        f'<h4 style="margin:0;color:#F8FAFC;">📈 Cognitive Progress — {_s(name)}</h4>'
        '<div style="font-size:0.8rem;color:#94A3B8;margin-top:0.2rem;">'
        'Actual recorded assessment scores — not projected or fabricated data</div>'
        '</div>'
    )

    assessments = assessment_repo.get_assessments_by_patient(patient_id, order_asc=True)

    if not assessments:
        _md(
            '<div class="aidaxis-card" style="text-align:center;padding:3rem 1.5rem;">'
            '<div style="font-size:2.5rem;margin-bottom:0.75rem;">📈</div>'
            '<div style="color:#F8FAFC;font-weight:600;font-size:1.1rem;">No assessment history found</div>'
            '<div style="color:#94A3B8;font-size:0.88rem;margin-top:0.4rem;">'
            'Charts will appear once the patient has completed at least one assessment.</div>'
            '</div>'
        )
        return

    dates, scores, pct_scores = [], [], []
    for rec in assessments:
        dt = parse_iso_date(rec["assessment_date"])
        dates.append(dt.strftime("%b %d, %Y") if dt else rec["assessment_date"])
        scores.append(float(rec["total_score"]))
        pct_scores.append(float(rec["percentage_score"]))

    count = len(assessments)
    avg = sum(scores) / count

    # ── Summary metric row ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _md(
            '<div class="aidaxis-card aidaxis-card-accent" style="padding:0.9rem 1rem;text-align:center;">'
            '<div class="aidaxis-stat-label">Assessments</div>'
            f'<div class="aidaxis-stat-val">{count}</div>'
            '</div>'
        )
    with col2:
        clr = _score_color(pct_scores[-1])
        _md(
            '<div class="aidaxis-card" style="padding:0.9rem 1rem;text-align:center;">'
            '<div class="aidaxis-stat-label">Latest Score</div>'
            f'<div class="aidaxis-stat-val" style="color:{clr};">{scores[-1]:.0f}/30</div>'
            '</div>'
        )
    with col3:
        if count >= 2:
            diff = scores[-1] - scores[-2]
            sign = "+" if diff > 0 else ""
            chg_col = "#14B8A6" if diff >= 0 else "#EF4444"
            _md(
                '<div class="aidaxis-card" style="padding:0.9rem 1rem;text-align:center;">'
                '<div class="aidaxis-stat-label">Latest Change</div>'
                f'<div class="aidaxis-stat-val" style="color:{chg_col};">{sign}{diff:.1f}</div>'
                '</div>'
            )
        else:
            _md(
                '<div class="aidaxis-card" style="padding:0.9rem 1rem;text-align:center;">'
                '<div class="aidaxis-stat-label">Latest Change</div>'
                '<div class="aidaxis-stat-val" style="color:#475569;">—</div>'
                '</div>'
            )
    with col4:
        _md(
            '<div class="aidaxis-card" style="padding:0.9rem 1rem;text-align:center;">'
            '<div class="aidaxis-stat-label">Average Score</div>'
            f'<div class="aidaxis-stat-val">{avg:.1f}/30</div>'
            '</div>'
        )

    # ── Score trend chart ──
    if _PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=scores,
            mode="lines+markers",
            name="Score (out of 30)",
            line=dict(color="#A78BFA", width=3),
            marker=dict(size=10, color="#A78BFA"),
            hovertemplate="<b>%{x}</b><br>Score: %{y:.0f}/30<extra></extra>",
        ))
        for ref_val, ref_label, ref_col in [
            (25, "Normal range ≥25", "#14B8A6"),
            (20, "Mild impairment threshold", "#F59E0B"),
        ]:
            fig.add_hline(
                y=ref_val, line_dash="dot", line_color=ref_col,
                annotation_text=ref_label, annotation_position="bottom right",
                annotation_font_color=ref_col, annotation_font_size=11,
            )
        fig.update_layout(
            paper_bgcolor="#151E2E", plot_bgcolor="#0F172A",
            font=dict(color="#CBD5E1", family="Plus Jakarta Sans, sans-serif"),
            xaxis=dict(showgrid=False, title="Assessment Date", color="#94A3B8"),
            yaxis=dict(showgrid=True, gridcolor="#1E293B", title="Score (out of 30)",
                       range=[0, 32], color="#94A3B8"),
            height=360, margin=dict(l=10, r=10, t=30, b=10), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        import pandas as pd
        df = pd.DataFrame({"Assessment Date": dates, "Score (out of 30)": scores})
        st.line_chart(df.set_index("Assessment Date"))

    # ── Domain breakdown for latest assessment ──
    latest = assessments[-1]
    domain_scores = latest.get("domain_scores", {})
    if domain_scores:
        st.markdown("#### 🧩 Latest Domain Breakdown")
        if _PLOTLY:
            d_names = [v.get("title", k) for k, v in domain_scores.items()]
            d_pcts = [v.get("percentage", 0) for v in domain_scores.values()]
            colors = [_score_color(p) for p in d_pcts]
            fig2 = go.Figure(go.Bar(
                x=d_pcts, y=d_names, orientation="h",
                marker_color=colors,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="#151E2E", plot_bgcolor="#0F172A",
                font=dict(color="#CBD5E1"),
                xaxis=dict(range=[0, 105], title="% Achieved", gridcolor="#1E293B"),
                yaxis=dict(autorange="reversed"),
                height=max(280, 42 * len(d_names)),
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            cols = st.columns(min(len(domain_scores), 4))
            for i, (dk, dv) in enumerate(domain_scores.items()):
                with cols[i % 4]:
                    p = dv.get("percentage", 0)
                    _md(
                        '<div class="aidaxis-card" style="padding:0.8rem;text-align:center;">'
                        f'<div style="font-size:0.75rem;color:#94A3B8;">{_s(dv.get("title", dk))}</div>'
                        f'<div style="font-size:1.2rem;font-weight:700;color:{_score_color(p)};">'
                        f'{dv.get("score", 0):.0f}/{dv.get("max_score", 1):.0f}</div>'
                        '</div>'
                    )

    # ── Full history table ──
    if count > 1:
        st.markdown("#### 📅 Full Assessment History")
        for rec in reversed(assessments):
            dt_str = _fmt_ts(rec["assessment_date"])
            score = rec["total_score"]
            pct = rec["percentage_score"]
            clr = _score_color(pct)
            notes_html = (
                f'<div style="font-size:0.8rem;color:#A78BFA;margin-top:0.1rem;">📝 {_s(rec["notes"])}</div>'
                if rec.get("notes") else ""
            )
            _md(
                '<div class="aidaxis-card" style="padding:0.8rem 1rem;margin-bottom:0.4rem;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<div>'
                f'<div style="font-size:0.9rem;font-weight:600;color:#F8FAFC;">{_s(dt_str)}'
                f'<span style="font-size:0.75rem;color:#64748B;margin-left:0.5rem;">'
                f'{_s(rec["assessment_id"])}</span></div>'
                + notes_html +
                '</div>'
                '<div style="text-align:right;min-width:70px;">'
                f'<span style="font-size:1.1rem;font-weight:700;color:{clr};">{score:.0f}</span>'
                f'<span style="font-size:0.8rem;color:#64748B;">/30</span>'
                f'<div style="font-size:0.75rem;color:#64748B;">{pct:.1f}%</div>'
                '</div>'
                '</div></div>'
            )

    _md(
        '<div class="aidaxis-disclaimer">'
        '<strong>Clinical Scope:</strong> Cognitive assessment scores are observational records only. '
        'Score changes over time do not constitute a diagnosis of Alzheimer\'s disease or confirm '
        'disease progression. All results should be reviewed by a qualified clinician.'
        '</div>'
    )


# ---------------------------------------------------------------------------
# C. Patient Record Management — read-only, same data as Document Vault
# ---------------------------------------------------------------------------

def _render_patient_records(patient_id: str, document_repo: DocumentRepository):
    profile = _PATIENT_PROFILES.get(patient_id, {})
    name = profile.get("name", patient_id)

    _md(
        '<div class="aidaxis-card aidaxis-card-accent" style="padding:1rem 1.25rem;margin-bottom:1rem;">'
        f'<h4 style="margin:0;color:#F8FAFC;">📁 Medical Records — {_s(name)}</h4>'
        '<div style="font-size:0.8rem;color:#94A3B8;margin-top:0.2rem;">'
        'Read-only view. Documents are uploaded by the patient via the Medical Document Vault.</div>'
        '</div>'
    )

    fc1, fc2 = st.columns([2, 3])
    with fc1:
        all_cats = ["All Categories"] + DOCUMENT_CATEGORIES
        sel_cat = st.selectbox(
            "Filter by Category", all_cats,
            index=all_cats.index(st.session_state["cg_doc_filter_cat"])
            if st.session_state["cg_doc_filter_cat"] in all_cats else 0,
            key="cg_cat_selector",
        )
        st.session_state["cg_doc_filter_cat"] = sel_cat
    with fc2:
        search = st.text_input(
            "Search records",
            value=st.session_state["cg_doc_search"],
            placeholder="Search by title or description…",
            key="cg_search_input",
        )
        st.session_state["cg_doc_search"] = search

    docs = document_repo.get_documents(patient_id, category=sel_cat, search=search)
    cat_counts = document_repo.get_categories_with_counts(patient_id)

    if not docs:
        msg = (
            "Try a different search or category filter."
            if (search or sel_cat != "All Categories")
            else "This patient has not uploaded any documents yet."
        )
        _md(
            '<div class="aidaxis-card" style="text-align:center;padding:2.5rem 1.5rem;">'
            '<div style="font-size:2.5rem;margin-bottom:0.75rem;">📂</div>'
            '<div style="color:#F8FAFC;font-weight:600;font-size:1.05rem;">No records found</div>'
            f'<div style="color:#94A3B8;font-size:0.88rem;margin-top:0.4rem;">{_s(msg)}</div>'
            '</div>'
        )
        return

    # Category pills
    pills = "".join(
        f'<span class="aidaxis-badge aidaxis-badge-violet" style="margin-right:0.4rem;">'
        f'{_category_icon(c)} {_s(c)}: {n}</span>'
        for c, n in cat_counts.items()
    )
    _md(f'<div style="margin-bottom:1rem;display:flex;flex-wrap:wrap;gap:0.3rem;">{pills}</div>')

    preview_id = st.session_state.get("cg_doc_preview_id")
    for doc in docs:
        _render_caregiver_doc_card(
            doc, patient_id, document_repo,
            show_preview=(preview_id == doc["doc_id"]),
        )


def _render_caregiver_doc_card(
    doc: dict,
    patient_id: str,
    document_repo: DocumentRepository,
    show_preview: bool,
):
    """Read-only document card with preview + download. All HTML via concatenation."""
    doc_id = doc["doc_id"]
    cat_icon = _category_icon(doc["category"])
    ext_badge = doc["file_type"].split("/")[-1].upper()
    doc_date_str = f"Doc date: {doc['document_date']}" if doc.get("document_date") else ""
    desc_html = (
        f'<div style="font-size:0.8rem;color:#A78BFA;margin-top:0.15rem;">📝 {_s(doc["description"])}</div>'
        if doc.get("description") else ""
    )

    upload_ts = _fmt_ts(doc["upload_timestamp"])

    _md(
        '<div class="aidaxis-card aidaxis-card-accent" style="margin-bottom:0.5rem;padding:0.9rem 1.1rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        '<div style="flex:1;min-width:0;">'
        f'<div style="font-size:1rem;font-weight:600;color:#F8FAFC;">📄 {_s(doc["title"])}</div>'
        f'<div style="font-size:0.82rem;color:#94A3B8;margin:0.18rem 0;">'
        f'{cat_icon} {_s(doc["category"])} &nbsp;·&nbsp; '
        f'{_fmt_bytes(doc["file_size_bytes"])} &nbsp;·&nbsp; Uploaded {_s(upload_ts)}</div>'
        + (f'<div style="font-size:0.8rem;color:#64748B;">{_s(doc_date_str)}</div>' if doc_date_str else "")
        + desc_html
        + '</div>'
        f'<span class="aidaxis-badge aidaxis-badge-violet">{_s(ext_badge)}</span>'
        '</div></div>'
    )

    c1, c2, c_space = st.columns([1, 1, 4])
    with c1:
        lbl = "🔒 Close" if show_preview else "👁️ Preview"
        if st.button(lbl, key=f"cg_prev_{doc_id}", use_container_width=True):
            st.session_state["cg_doc_preview_id"] = None if show_preview else doc_id
            st.rerun()
    with c2:
        file_bytes = document_repo.get_file_bytes(doc_id, patient_id)
        if file_bytes:
            mime = _mime_for_download(doc["file_type"], doc["original_filename"])
            st.download_button(
                "⬇️ Download", data=file_bytes,
                file_name=doc["original_filename"], mime=mime,
                key=f"cg_dl_{doc_id}", use_container_width=True,
            )
        else:
            st.button(
                "⬇️ Download", key=f"cg_dl_na_{doc_id}",
                disabled=True, use_container_width=True,
                help="File not found on disk.",
            )

    if show_preview:
        _render_cg_preview(doc, patient_id, document_repo)


def _render_cg_preview(doc: dict, patient_id: str, document_repo: DocumentRepository):
    ext = doc["original_filename"].rsplit(".", 1)[-1].lower()
    file_bytes = document_repo.get_file_bytes(doc["doc_id"], patient_id)
    if not file_bytes:
        st.warning("⚠️ File not found on disk.")
        return
    _md(
        '<div style="background:#0F172A;border:1px solid #233148;border-radius:10px;'
        'padding:1rem;margin-bottom:0.75rem;">'
        '<div style="color:#94A3B8;font-size:0.8rem;margin-bottom:0.5rem;">'
        f'Preview: <strong style="color:#F8FAFC;">{_s(doc["title"])}</strong></div>'
    )
    if ext in ("jpg", "jpeg", "png"):
        st.image(file_bytes, use_container_width=True)
    elif ext == "pdf":
        b64 = base64.b64encode(file_bytes).decode()
        _md(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="520px" style="border:none;border-radius:6px;"></iframe>'
        )
    else:
        st.info("Preview not supported for this file type. Use Download instead.")
    _md("</div>")
