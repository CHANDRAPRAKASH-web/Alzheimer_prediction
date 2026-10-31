"""
=========================================================
Aid Axis — Cognitive Health & NeuroVision AI Platform

Unified Healthcare Platform integrating:
1. NeuroVision AI — Deep Learning Brain MRI Analysis & Grad-CAM
2. Cognitive Health Engine — Longitudinal Cognitive Assessment,
   Tracking, Progression Analytics & Digital Twin Prototype.
3. Memory Intelligence Hub — AI-powered scheduling companion.
4. Medical Document Vault — Secure patient document management.
5. Caregiver Dashboard — Patient overview, cognitive progress,
   and read-only medical record access.

Author  : CP & Aid Axis Development Team
Project : Aid Axis
=========================================================
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# Healthcare Theme & Styles
from app.cognitive.styles import apply_healthcare_theme

# Database & Repositories
from database.repository import AssessmentRepository
from database.event_repository import EventRepository
from database.document_repository import DocumentRepository

# Modules
from app.neurovision import render_neurovision
from app.cognitive.overview import render_cognitive_overview
from app.cognitive.assessment_flow import render_assessment_wizard, reset_assessment
from app.cognitive.history import render_assessment_history
from app.cognitive.dashboard import render_progress_dashboard
from app.cognitive.analytics import render_progression_analytics
from app.cognitive.digital_twin import render_cognitive_digital_twin
from app.memory_hub import render_memory_intelligence_hub
from app.document_vault import render_document_vault
from app.caregiver_dashboard import render_caregiver_dashboard


# =========================================================
# Page Configuration
# =========================================================
st.set_page_config(
    page_title="Aid Axis — Cognitive Health Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# Cached resource singletons
# =========================================================

@st.cache_resource
def get_repository() -> AssessmentRepository:
    return AssessmentRepository()


@st.cache_resource
def get_event_repository() -> EventRepository:
    return EventRepository()


@st.cache_resource
def get_document_repository() -> DocumentRepository:
    return DocumentRepository()


# =========================================================
# Navigation constants
# =========================================================
_ALL_MODULES = [
    "🧠 NeuroVision AI (MRI Analysis)",
    "📋 Cognitive Health Engine",
    "🗓️ Memory Intelligence Hub",
    "🗂️ Medical Document Vault",
    "👩‍⚕️ Caregiver Dashboard",
]

_COGNITIVE_SUBPAGES = [
    "Overview",
    "New Assessment",
    "Assessment History",
    "Progress Dashboard",
    "Progression Analytics",
    "Cognitive Digital Twin",
]


def main():
    # ---------------------------------------------------------
    # Apply Unified Healthcare Styling
    # ---------------------------------------------------------
    apply_healthcare_theme()

    repository = get_repository()
    event_repository = get_event_repository()
    document_repository = get_document_repository()

    # ---------------------------------------------------------
    # Sidebar: Brand, Patient ID, and Navigation
    # ---------------------------------------------------------
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0 1rem 0;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 2rem;">🧠</span>
                    <div>
                        <h2 style="margin: 0; font-size: 1.4rem; color: #F8FAFC; letter-spacing: -0.02em;">AID AXIS</h2>
                        <div style="font-size: 0.75rem; color: #A78BFA; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">
                            Cognitive Health Platform
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # Patient Profile Management
        st.markdown("##### 👤 Patient Profile")
        existing_patients = repository.get_all_patients()
        default_patient = "PATIENT-001"
        if default_patient not in existing_patients:
            existing_patients.append(default_patient)

        patient_mode = st.radio(
            "Profile Selection",
            ["Select Existing", "Enter New ID"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )

        if patient_mode == "Select Existing":
            selected_patient = st.selectbox(
                "Active Patient Identifier:",
                existing_patients,
                index=existing_patients.index(
                    st.session_state.get("active_patient_id", default_patient)
                ) if st.session_state.get("active_patient_id", default_patient) in existing_patients else 0
            )
            st.session_state["active_patient_id"] = selected_patient
        else:
            new_id = st.text_input(
                "Enter New Patient Identifier:",
                value="",
                placeholder="e.g., PATIENT-002"
            ).strip().upper()
            if new_id:
                st.session_state["active_patient_id"] = new_id
            else:
                st.session_state["active_patient_id"] = default_patient

        active_patient = st.session_state["active_patient_id"]

        st.divider()

        # Main Module Navigation
        st.markdown("##### 🧭 Navigation")

        cur_module = st.session_state.get("primary_module", _ALL_MODULES[0])
        if cur_module not in _ALL_MODULES:
            cur_module = _ALL_MODULES[0]

        primary_module = st.radio(
            "Primary Module",
            _ALL_MODULES,
            index=_ALL_MODULES.index(cur_module),
            key="primary_module"
        )

        # Sub-navigation for Cognitive Health Engine
        if primary_module == "📋 Cognitive Health Engine":
            st.markdown("###### Cognitive Engine Sections:")
            cur_sub = st.session_state.get("cognitive_subpage", "Overview")
            sub_idx = _COGNITIVE_SUBPAGES.index(cur_sub) if cur_sub in _COGNITIVE_SUBPAGES else 0
            st.radio(
                "Subpage",
                _COGNITIVE_SUBPAGES,
                index=sub_idx,
                key="cognitive_subpage",
                label_visibility="collapsed"
            )

        st.divider()

        # Privacy notice
        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #64748B; line-height: 1.4;">
                <strong style="color: #94A3B8;">Prototype Notice:</strong><br/>
                For investigational and observational use only.
                Data is isolated per patient ID in local parameterised SQLite storage.
                Not an FDA/CE-cleared diagnostic device.
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # Main Content Router
    # ---------------------------------------------------------
    if primary_module == "🧠 NeuroVision AI (MRI Analysis)":
        render_neurovision()

    elif primary_module == "📋 Cognitive Health Engine":
        subpage = st.session_state.get("cognitive_subpage", "Overview")

        def navigate_to_assessment():
            reset_assessment()
            st.session_state["cognitive_subpage"] = "New Assessment"
            st.rerun()

        if subpage == "Overview":
            render_cognitive_overview(
                patient_id=active_patient,
                repository=repository,
                on_start_assessment=navigate_to_assessment
            )
        elif subpage == "New Assessment":
            render_assessment_wizard(patient_id=active_patient, repository=repository)
        elif subpage == "Assessment History":
            render_assessment_history(patient_id=active_patient, repository=repository)
        elif subpage == "Progress Dashboard":
            render_progress_dashboard(patient_id=active_patient, repository=repository)
        elif subpage == "Progression Analytics":
            render_progression_analytics(patient_id=active_patient, repository=repository)
        elif subpage == "Cognitive Digital Twin":
            render_cognitive_digital_twin(patient_id=active_patient, repository=repository)

    elif primary_module == "🗓️ Memory Intelligence Hub":
        render_memory_intelligence_hub(
            patient_id=active_patient,
            repository=event_repository,
            tz_name="Asia/Kolkata"
        )

    elif primary_module == "🗂️ Medical Document Vault":
        render_document_vault(
            patient_id=active_patient,
            repository=document_repository,
        )

    elif primary_module == "👩‍⚕️ Caregiver Dashboard":
        render_caregiver_dashboard(
            assessment_repo=repository,
            document_repo=document_repository,
        )


if __name__ == "__main__":
    main()