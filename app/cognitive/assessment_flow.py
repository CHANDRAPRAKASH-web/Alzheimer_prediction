"""
=========================================================
Aid Axis - Structured Cognitive Assessment Workflow

Guided step-by-step cognitive assessment wizard:
- Clearly separated domain steps
- High contrast, large readable controls
- Step validation with friendly error hints
- Previous & Next navigation controls
- Review screen before final submission
- Double confirmation before persistence
- Strict prevention of accidental duplicate submissions
- Transparent completion summary with domain scores
=========================================================
"""

import uuid
import streamlit as st
from datetime import datetime, timezone
from typing import Dict, Any

from services.assessment_service import (
    DOMAINS,
    TARGET_REGISTRATION_WORDS,
    validate_step,
    calculate_assessment_score,
    INSTRUMENT_NAME,
    INSTRUMENT_VERSION
)
from database.repository import AssessmentRepository


def init_assessment_state():
    """
    Initializes session state keys for the assessment wizard.
    """
    if "assess_step" not in st.session_state:
        st.session_state["assess_step"] = 0
    if "assess_responses" not in st.session_state:
        st.session_state["assess_responses"] = {
            "time_year": "",
            "time_season": "Autumn",
            "time_month": "",
            "time_date": "",
            "time_day": "",
            "place_country": "",
            "place_state": "",
            "place_city": "",
            "place_setting": "Home",
            "place_room": "",
            "registration_words": [],
            "attention_mode": "serial7",
            "attention_serial7": ["", "", "", "", ""],
            "attention_spelling": ["", "", "", "", ""],
            "recall_words": [],
            "lang_naming_1": "",
            "lang_naming_2": "",
            "lang_repetition": "",
            "lang_fluency": "",
            "comp_step_1": False,
            "comp_step_2": False,
            "comp_step_3": False,
            "visuo_pentagon": "",
            "visuo_clock": "",
            "notes": ""
        }
    if "assess_completed" not in st.session_state:
        st.session_state["assess_completed"] = False
    if "assess_result" not in st.session_state:
        st.session_state["assess_result"] = None
    if "assess_submitted_id" not in st.session_state:
        st.session_state["assess_submitted_id"] = None
    if "assess_step_errors" not in st.session_state:
        st.session_state["assess_step_errors"] = []


def reset_assessment():
    """
    Resets assessment state to restart or start fresh.
    """
    st.session_state["assess_step"] = 0
    st.session_state["assess_responses"] = {
        "time_year": "",
        "time_season": "Autumn",
        "time_month": "",
        "time_date": "",
        "time_day": "",
        "place_country": "",
        "place_state": "",
        "place_city": "",
        "place_setting": "Home",
        "place_room": "",
        "registration_words": [],
        "attention_mode": "serial7",
        "attention_serial7": ["", "", "", "", ""],
        "attention_spelling": ["", "", "", "", ""],
        "recall_words": [],
        "lang_naming_1": "",
        "lang_naming_2": "",
        "lang_repetition": "",
        "lang_fluency": "",
        "comp_step_1": False,
        "comp_step_2": False,
        "comp_step_3": False,
        "visuo_pentagon": "",
        "visuo_clock": "",
        "notes": ""
    }
    st.session_state["assess_completed"] = False
    st.session_state["assess_result"] = None
    st.session_state["assess_submitted_id"] = None
    st.session_state["assess_step_errors"] = []


def render_assessment_wizard(patient_id: str, repository: AssessmentRepository):
    """
    Main renderer for the interactive structured cognitive questionnaire.
    """
    init_assessment_state()

    st.markdown("## 📝 Cognitive Monitoring Questionnaire — Prototype")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 0.95rem; margin-top: -0.4rem;'>"
        "Standardized multi-domain screening & tracking protocol. "
        "<strong>Note:</strong> Research prototype; does not diagnose dementia or Alzheimer's disease."
        "</p>",
        unsafe_allow_html=True
    )

    # If completed, show summary screen
    if st.session_state["assess_completed"] and st.session_state["assess_result"]:
        render_completion_summary(patient_id, repository)
        return

    total_steps = len(DOMAINS) + 1  # 8 domain steps + 1 review step
    curr_step = st.session_state["assess_step"]

    # Header / Step Tracker
    progress_val = min(float(curr_step) / float(total_steps - 1), 1.0)
    st.progress(progress_val)

    if curr_step < len(DOMAINS):
        domain = DOMAINS[curr_step]
        st.markdown(
            f"""
            <div class="step-container">
                <div>
                    <span class="aidaxis-badge aidaxis-badge-violet">Step {curr_step + 1} of {len(DOMAINS)}</span>
                    <h3 style="margin: 0.4rem 0 0.1rem 0; color: #F8FAFC;">{domain['icon']} {domain['title']}</h3>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{domain['description']} (Max: {domain['max_score']:.0f} pts)</div>
                </div>
                <div style="text-align: right; font-size: 0.85rem; color: #64748B;">
                    Patient: <strong style="color: #CBD5E1;">{patient_id}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="step-container">
                <div>
                    <span class="aidaxis-badge aidaxis-badge-teal">Final Review</span>
                    <h3 style="margin: 0.4rem 0 0.1rem 0; color: #F8FAFC;">🔍 Review Answers & Confirm</h3>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Review all recorded responses before calculating and saving score.</div>
                </div>
                <div style="text-align: right; font-size: 0.85rem; color: #64748B;">
                    Patient: <strong style="color: #CBD5E1;">{patient_id}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render any step errors
    if st.session_state["assess_step_errors"]:
        for err in st.session_state["assess_step_errors"]:
            st.warning(f"⚠️ {err}")

    # Render Step Content
    resp = st.session_state["assess_responses"]

    if curr_step == 0:
        render_step_time(resp)
    elif curr_step == 1:
        render_step_place(resp)
    elif curr_step == 2:
        render_step_registration(resp)
    elif curr_step == 3:
        render_step_attention(resp)
    elif curr_step == 4:
        render_step_delayed_recall(resp)
    elif curr_step == 5:
        render_step_language(resp)
    elif curr_step == 6:
        render_step_comprehension(resp)
    elif curr_step == 7:
        render_step_visuospatial(resp)
    elif curr_step == 8:
        render_step_review(resp, patient_id, repository)

    # Navigation Controls (Previous, Next, Cancel)
    if curr_step < 8:
        st.divider()
        col_prev, col_mid, col_next = st.columns([1, 2, 1])

        with col_prev:
            if curr_step > 0:
                if st.button("⬅️ Previous", key="btn_prev", use_container_width=True):
                    st.session_state["assess_step_errors"] = []
                    st.session_state["assess_step"] -= 1
                    st.rerun()

        with col_mid:
            if st.button("Cancel Assessment", key="btn_cancel", use_container_width=True):
                reset_assessment()
                st.rerun()

        with col_next:
            next_label = "Proceed to Review ➡️" if curr_step == 7 else "Next Step ➡️"
            if st.button(next_label, type="primary", key="btn_next", use_container_width=True):
                is_valid, errors = validate_step(curr_step, resp)
                if is_valid:
                    st.session_state["assess_step_errors"] = []
                    st.session_state["assess_step"] += 1
                    st.rerun()
                else:
                    st.session_state["assess_step_errors"] = errors
                    st.rerun()


# =========================================================
# Step 0: Orientation to Time
# =========================================================
def render_step_time(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <p style="color: #CBD5E1; font-size: 0.95rem; margin-bottom: 1.25rem;">
                Please ask the user or enter current temporal orientation details. 
                Exact answers or within acceptable clinical tolerance will be validated.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        resp["time_year"] = st.text_input(
            "1. What is the current year? (e.g., 2026)",
            value=resp.get("time_year", ""),
            placeholder="YYYY"
        )
        season_opts = ["Spring", "Summer", "Autumn", "Winter"]
        cur_season = resp.get("time_season", "Autumn")
        s_idx = season_opts.index(cur_season) if cur_season in season_opts else 0
        resp["time_season"] = st.selectbox(
            "2. What is the current season?",
            season_opts,
            index=s_idx
        )
        resp["time_month"] = st.text_input(
            "3. What is the current month? (e.g., October)",
            value=resp.get("time_month", ""),
            placeholder="Month name"
        )

    with col2:
        resp["time_date"] = st.text_input(
            "4. What is today's date of the month? (1-31)",
            value=resp.get("time_date", ""),
            placeholder="DD"
        )
        days_opts = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        cur_day = resp.get("time_day", "")
        d_idx = days_opts.index(cur_day) if cur_day in days_opts else 0
        resp["time_day"] = st.selectbox(
            "5. What day of the week is it today?",
            days_opts,
            index=d_idx
        )


# =========================================================
# Step 1: Orientation to Place
# =========================================================
def render_step_place(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <p style="color: #CBD5E1; font-size: 0.95rem; margin-bottom: 1.25rem;">
                Assess current geographical and environmental orientation.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        resp["place_country"] = st.text_input(
            "1. What country are we in?",
            value=resp.get("place_country", ""),
            placeholder="e.g., United States / India / Canada"
        )
        resp["place_state"] = st.text_input(
            "2. What state or province are we in?",
            value=resp.get("place_state", ""),
            placeholder="e.g., California / Ontario / Maharashtra"
        )
        resp["place_city"] = st.text_input(
            "3. What town or city are we in?",
            value=resp.get("place_city", ""),
            placeholder="City / municipality"
        )

    with col2:
        setting_opts = ["Home", "Clinic / Office", "Hospital", "Community Center", "Other"]
        cur_set = resp.get("place_setting", "Home")
        set_idx = setting_opts.index(cur_set) if cur_set in setting_opts else 0
        resp["place_setting"] = st.selectbox(
            "4. What type of building or setting is this?",
            setting_opts,
            index=set_idx
        )
        resp["place_room"] = st.text_input(
            "5. What room or floor are we on?",
            value=resp.get("place_room", ""),
            placeholder="e.g., Living Room / Floor 2"
        )


# =========================================================
# Step 2: Immediate Registration
# =========================================================
def render_step_registration(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card aidaxis-card-accent">
            <h4 style="color: #F8FAFC; margin-bottom: 0.5rem;">Encoding Stimulus</h4>
            <p style="color: #CBD5E1; font-size: 0.95rem;">
                Read the following 3 words aloud clearly, one second per word:
            </p>
            <div style="display: flex; gap: 1rem; margin: 1rem 0;">
                <span class="aidaxis-badge aidaxis-badge-violet" style="font-size: 1.1rem; padding: 0.5rem 1rem;">🍎 APPLE</span>
                <span class="aidaxis-badge aidaxis-badge-violet" style="font-size: 1.1rem; padding: 0.5rem 1rem;">🪑 TABLE</span>
                <span class="aidaxis-badge aidaxis-badge-violet" style="font-size: 1.1rem; padding: 0.5rem 1rem;">🪙 PENNY</span>
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem;">
                Instruct the participant: <em>"Listen carefully. I am going to say three words. 
                Please repeat them back to me now, and remember them because I will ask you to recall them later."</em>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("##### Immediate Repeat Verification:")
    st.write("Check all words correctly repeated on the first trial (1 point each):")

    c1, c2, c3 = st.columns(3)
    cur_words = resp.get("registration_words", [])

    with c1:
        apple = st.checkbox("🍎 Apple", value=("apple" in cur_words), key="reg_apple")
    with c2:
        table = st.checkbox("🪑 Table", value=("table" in cur_words), key="reg_table")
    with c3:
        penny = st.checkbox("🪙 Penny", value=("penny" in cur_words), key="reg_penny")

    new_words = []
    if apple:
        new_words.append("apple")
    if table:
        new_words.append("table")
    if penny:
        new_words.append("penny")
    resp["registration_words"] = new_words


# =========================================================
# Step 3: Attention & Calculation
# =========================================================
def render_step_attention(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <p style="color: #CBD5E1; font-size: 0.95rem;">
                Select one of the two standard attention tasks below (5 points maximum):
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    mode = st.radio(
        "Select Attention Task Mode:",
        ["Option A: Serial 7s Subtraction (100 - 7)", "Option B: Spell 'WORLD' Backwards"],
        index=0 if resp.get("attention_mode", "serial7") == "serial7" else 1
    )

    if mode.startswith("Option A"):
        resp["attention_mode"] = "serial7"
        st.markdown(
            """
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Ask the participant to count backwards from 100 by sevens for 5 steps.
            </p>
            """,
            unsafe_allow_html=True
        )
        cur_seq = resp.get("attention_serial7", ["", "", "", "", ""])
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                cur_val = cur_seq[i] if i < len(cur_seq) else ""
                cur_seq[i] = st.text_input(
                    f"Step {i+1}:",
                    value=cur_val,
                    placeholder=f"Answer {i+1}",
                    key=f"ser7_{i}"
                )
        resp["attention_serial7"] = cur_seq
    else:
        resp["attention_mode"] = "spelling"
        st.markdown(
            """
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Ask the participant to spell the word <strong>WORLD</strong> backwards. 
                Record each letter in sequence:
            </p>
            """,
            unsafe_allow_html=True
        )
        cur_letters = resp.get("attention_spelling", ["", "", "", "", ""])
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                cur_val = cur_letters[i] if i < len(cur_letters) else ""
                cur_letters[i] = st.text_input(
                    f"Letter {i+1}:",
                    value=cur_val,
                    max_chars=1,
                    placeholder=f"Pos {i+1}",
                    key=f"spell_{i}"
                )
        resp["attention_spelling"] = cur_letters


# =========================================================
# Step 4: Delayed Recall
# =========================================================
def render_step_delayed_recall(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card aidaxis-card-accent">
            <h4 style="color: #F8FAFC; margin-bottom: 0.5rem;">Short-Term Memory Retrieval</h4>
            <p style="color: #CBD5E1; font-size: 0.95rem;">
                Instruct the participant: <em>"What were the three words I asked you to remember a few moments ago?"</em>
            </p>
            <p style="color: #94A3B8; font-size: 0.85rem;">
                Do not provide hints or clues during spontaneous recall. Mark each word successfully retrieved.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("##### Spontaneous Recall Verification:")
    c1, c2, c3 = st.columns(3)
    cur_recall = resp.get("recall_words", [])

    with c1:
        apple = st.checkbox("🍎 Apple recalled", value=("apple" in cur_recall), key="rec_apple")
    with c2:
        table = st.checkbox("🪑 Table recalled", value=("table" in cur_recall), key="rec_table")
    with c3:
        penny = st.checkbox("🪙 Penny recalled", value=("penny" in cur_recall), key="rec_penny")

    new_recall = []
    if apple:
        new_recall.append("apple")
    if table:
        new_recall.append("table")
    if penny:
        new_recall.append("penny")
    resp["recall_words"] = new_recall

    if not new_recall:
        st.info("ℹ️ If the participant was unable to recall any of the words, leave checkboxes unmarked and proceed.")


# =========================================================
# Step 5: Language & Naming
# =========================================================
def render_step_language(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <p style="color: #CBD5E1; font-size: 0.95rem; margin-bottom: 1.25rem;">
                Evaluate confrontation naming, phrase repetition, and categorical fluency.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        resp["lang_naming_1"] = st.text_input(
            "1. Naming: What object is worn on the wrist to tell time?",
            value=resp.get("lang_naming_1", ""),
            placeholder="e.g., Watch"
        )
        resp["lang_naming_2"] = st.text_input(
            "2. Naming: What handheld writing instrument uses ink?",
            value=resp.get("lang_naming_2", ""),
            placeholder="e.g., Pen"
        )

    with col2:
        resp["lang_repetition"] = st.text_input(
            "3. Repetition: Repeat the exact phrase: 'No ifs, ands, or buts.'",
            value=resp.get("lang_repetition", ""),
            placeholder="Enter repeated phrase"
        )
        resp["lang_fluency"] = st.text_input(
            "4. Fluency: Name any common animal (e.g., elephant, tiger, dog)",
            value=resp.get("lang_fluency", ""),
            placeholder="Animal name"
        )


# =========================================================
# Step 6: Comprehension & Execution
# =========================================================
def render_step_comprehension(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <h4 style="color: #F8FAFC; margin-bottom: 0.5rem;">Multi-Step Instruction Comprehension</h4>
            <p style="color: #CBD5E1; font-size: 0.95rem;">
                Instruct the participant: <em>"Follow these three commands in order:"</em>
            </p>
            <ol style="color: #94A3B8; font-size: 0.9rem; padding-left: 1.25rem; line-height: 1.6;">
                <li>Take a piece of paper in your right hand.</li>
                <li>Fold it in half once.</li>
                <li>Place it gently on the table.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("##### Execution Adherence Checks (1 point each):")
    resp["comp_step_1"] = st.checkbox(
        "Step 1: Took paper in right hand accurately",
        value=resp.get("comp_step_1", False),
        key="chk_comp1"
    )
    resp["comp_step_2"] = st.checkbox(
        "Step 2: Folded the paper in half correctly",
        value=resp.get("comp_step_2", False),
        key="chk_comp2"
    )
    resp["comp_step_3"] = st.checkbox(
        "Step 3: Placed paper on the table / surface",
        value=resp.get("comp_step_3", False),
        key="chk_comp3"
    )


# =========================================================
# Step 7: Visuospatial & Executive
# =========================================================
def render_step_visuospatial(resp: Dict[str, Any]):
    st.markdown(
        """
        <div class="aidaxis-card">
            <h4 style="color: #F8FAFC; margin-bottom: 0.5rem;">Visual & Spatial Reasoning</h4>
            <p style="color: #CBD5E1; font-size: 0.95rem;">
                Select the correct options for spatial configuration and visual time-telling.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Question 1: Intersecting shape identification
    st.markdown("##### 1. Intersecting Geometric Figure Recognition")
    st.write(
        "Which description represents two intersecting five-sided pentagons forming a 4-sided overlap?"
    )
    pent_opts = [
        "",
        "Option A: Two adjacent circles touching at a single perimeter point",
        "Option B: Intersecting 5-sided pentagons with a 4-sided diamond intersection",
        "Option C: Two non-overlapping concentric squares",
        "Option D: A single hexagon with an internal line"
    ]
    cur_p = resp.get("visuo_pentagon", "")
    p_idx = pent_opts.index(cur_p) if cur_p in pent_opts else 0
    resp["visuo_pentagon"] = st.selectbox(
        "Select matching geometric pattern:",
        pent_opts,
        index=p_idx,
        key="sel_pent"
    )

    st.divider()

    # Question 2: Clock face time representation
    st.markdown("##### 2. Analog Clock Face Configuration")
    st.write(
        "If a clock displays '10 minutes past 11', what are the positions of the hands?"
    )
    clock_opts = [
        "",
        "Option A: Hour hand pointing near 11, minute hand pointing exactly at 2",
        "Option B: Hour hand pointing at 2, minute hand pointing at 11",
        "Option C: Both hands pointing directly at 12",
        "Option D: Hour hand pointing at 10, minute hand pointing at 11"
    ]
    cur_c = resp.get("visuo_clock", "")
    c_idx = clock_opts.index(cur_c) if cur_c in clock_opts else 0
    resp["visuo_clock"] = st.selectbox(
        "Select the correct clock hand configuration:",
        clock_opts,
        index=c_idx,
        key="sel_clock"
    )


# =========================================================
# Step 8: Review & Confirmation
# =========================================================
def render_step_review(
    resp: Dict[str, Any],
    patient_id: str,
    repository: AssessmentRepository
):
    st.markdown("### 📋 Review Recorded Answers")
    st.write("Please verify all recorded responses before calculating and storing the final score.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">1. Orientation: Time</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Year: <strong>{resp.get('time_year') or 'Not recorded'}</strong><br/>
                    • Season: <strong>{resp.get('time_season')}</strong><br/>
                    • Month: <strong>{resp.get('time_month') or 'Not recorded'}</strong><br/>
                    • Date: <strong>{resp.get('time_date') or 'Not recorded'}</strong><br/>
                    • Day: <strong>{resp.get('time_day') or 'Not recorded'}</strong>
                </div>
            </div>
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">2. Orientation: Place</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Country: <strong>{resp.get('place_country') or 'Not recorded'}</strong><br/>
                    • State: <strong>{resp.get('place_state') or 'Not recorded'}</strong><br/>
                    • City: <strong>{resp.get('place_city') or 'Not recorded'}</strong><br/>
                    • Setting: <strong>{resp.get('place_setting')}</strong><br/>
                    • Room: <strong>{resp.get('place_room') or 'Not recorded'}</strong>
                </div>
            </div>
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">3. Registration & Delayed Recall</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Immediate: <strong>{', '.join(resp.get('registration_words', [])) or 'None'}</strong><br/>
                    • Delayed: <strong>{', '.join(resp.get('recall_words', [])) or 'None'}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">4. Attention Task</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Mode: <strong>{resp.get('attention_mode')}</strong><br/>
                    • Entries: <strong>{', '.join(resp.get('attention_serial7' if resp.get('attention_mode') == 'serial7' else 'attention_spelling', []))}</strong>
                </div>
            </div>
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">5. Language & Execution</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Naming: <strong>{resp.get('lang_naming_1')}, {resp.get('lang_naming_2')}</strong><br/>
                    • Repetition: <strong>{resp.get('lang_repetition')}</strong><br/>
                    • Fluency: <strong>{resp.get('lang_fluency')}</strong><br/>
                    • Comprehension: <strong>{sum([1 for s in ['comp_step_1', 'comp_step_2', 'comp_step_3'] if resp.get(s)])} / 3 steps completed</strong>
                </div>
            </div>
            <div class="aidaxis-card">
                <div class="aidaxis-stat-label">6. Visuospatial</div>
                <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.6;">
                    • Pattern: <strong>{resp.get('visuo_pentagon')[:35]}...</strong><br/>
                    • Clock: <strong>{resp.get('visuo_clock')[:35]}...</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Optional Examiner Notes
    resp["notes"] = st.text_area(
        "Optional Clinical / Observational Notes:",
        value=resp.get("notes", ""),
        placeholder="Enter notes on participant engagement, fatigue, or ambient distractions...",
        height=80
    )

    st.markdown(
        """
        <div class="aidaxis-notice">
            <strong>Idempotency Safeguard:</strong> Submitting will lock and record this assessment with a 
            unique UUID. Duplicate records and accidental re-submissions are strictly guarded against.
        </div>
        """,
        unsafe_allow_html=True
    )

    col_back, col_submit = st.columns([1, 2])
    with col_back:
        if st.button("⬅️ Back to Editing", use_container_width=True):
            st.session_state["assess_step"] = 7
            st.rerun()

    with col_submit:
        if st.button("✅ Confirm & Save Assessment", type="primary", use_container_width=True):
            # Compute score strictly from responses
            score_data = calculate_assessment_score(resp)
            assessment_id = f"COG-{uuid.uuid4().hex[:12].upper()}"

            record = {
                "assessment_id": assessment_id,
                "patient_id": patient_id,
                "assessment_type": INSTRUMENT_NAME,
                "assessment_version": INSTRUMENT_VERSION,
                "assessment_date": datetime.now(timezone.utc).isoformat(),
                "total_score": score_data["total_score"],
                "max_score": score_data["max_score"],
                "percentage_score": score_data["percentage_score"],
                "domain_scores": score_data["domain_scores"],
                "responses": resp,
                "notes": resp.get("notes", ""),
                "metadata": {
                    "source": "Aid Axis Streamlit Wizard",
                    "scoring_engine": "deterministic-v1.0"
                }
            }

            # Save via repository (handles idempotency & duplicate checks)
            success = repository.save_assessment(record)
            if success:
                st.session_state["assess_completed"] = True
                st.session_state["assess_result"] = record
                st.session_state["assess_submitted_id"] = assessment_id
                st.rerun()
            else:
                st.error("Submission was prevented because this assessment ID was already recorded.")


# =========================================================
# Completion Summary
# =========================================================
def render_completion_summary(patient_id: str, repository: AssessmentRepository):
    """
    Renders the post-assessment score summary and options.
    """
    record = st.session_state["assess_result"]
    total = record.get("total_score", 0.0)
    max_s = record.get("max_score", 30.0)
    pct = record.get("percentage_score", 0.0)
    aid = record.get("assessment_id", "")

    st.markdown(
        f"""
        <div class="aidaxis-card aidaxis-card-teal" style="text-align: center; padding: 2rem 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
            <h2 style="color: #F8FAFC; margin-bottom: 0.25rem;">Assessment Completed & Saved</h2>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Record ID: <span style="color: #A78BFA; font-family: monospace;">{aid}</span> &nbsp;|&nbsp; 
                Patient: <span style="color: #CBD5E1;">{patient_id}</span>
            </div>
            <div style="display: inline-block; background: #0F1626; border: 1px solid #233148; border-radius: 12px; padding: 1.25rem 2.5rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; color: #94A3B8; text-transform: uppercase;">Total Score</div>
                <div style="font-size: 3rem; font-weight: 700; color: #F8FAFC; line-height: 1.1;">
                    {total:.1f} <span style="font-size: 1.25rem; color: #64748B;">/ {max_s:.0f}</span>
                </div>
                <div style="color: #14B8A6; font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem;">
                    {pct:.1f}% Performance Score
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Domain Breakdown:")
    domains = record.get("domain_scores", {})
    cols = st.columns(min(len(domains), 4))
    for idx, (dom_id, dom_data) in enumerate(domains.items()):
        col = cols[idx % 4]
        with col:
            s = dom_data.get("score", 0.0)
            m = dom_data.get("max_score", 1.0)
            st.markdown(
                f"""
                <div class="aidaxis-card" style="padding: 0.75rem 1rem;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">{dom_data.get('title', dom_id)}</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #F8FAFC;">
                        {s:.1f} / {m:.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 View Progress Dashboard", type="primary", use_container_width=True):
            st.session_state["cognitive_subpage"] = "Progress Dashboard"
            reset_assessment()
            st.rerun()
    with c2:
        if st.button("➕ Start Another Assessment", use_container_width=True):
            reset_assessment()
            st.rerun()

    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Notice:</strong> This score has been committed to the local database. 
            It reflects performance on the prototype screening instrument only and is not a clinical diagnosis.
        </div>
        """,
        unsafe_allow_html=True
    )
