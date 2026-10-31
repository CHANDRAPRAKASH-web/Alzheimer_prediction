"""
=========================================================
Aid Axis - Memory Intelligence Hub

Dual-Panel Healthcare Interface:
1. Left Panel: Aid Axis Memory Companion (Conversational Chatbot with Groq LLM & Tools)
2. Right Panel: My Schedule (Synchronized daily routine timeline & manual management)
=========================================================
"""

import html as _html_module
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List

from database.event_repository import EventRepository
from services.datetime_service import (
    get_current_local_datetime,
    format_friendly_date,
    format_friendly_time,
)
from services.groq_service import (
    run_memory_companion_chat,
    get_groq_api_key,
    get_groq_model_id,
)
from app.cognitive.styles import render_metric_card


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(value) -> str:
    """HTML-escape a value so it is safe to embed inside st.markdown HTML blocks."""
    return _html_module.escape(str(value)) if value is not None else ""


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

def init_memory_hub_state():
    """Initialises session state keys for the Memory Intelligence Hub."""
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I am your **Aid Axis Memory Companion**. "
                    "You can tell me about appointments, activities, or ask what is scheduled today. "
                    "How can I assist you?"
                ),
            }
        ]
    if "editing_event_id" not in st.session_state:
        st.session_state["editing_event_id"] = None
    if "pending_cancel_event_id" not in st.session_state:
        st.session_state["pending_cancel_event_id"] = None
    if "schedule_tab" not in st.session_state:
        st.session_state["schedule_tab"] = "Today"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_memory_intelligence_hub(
    patient_id: str,
    repository: EventRepository,
    tz_name: str = "Asia/Kolkata",
):
    """Renders the unified dual-panel Memory Intelligence Hub."""
    init_memory_hub_state()

    # Top Header & Status Bar
    st.markdown("## 🗓️ Memory Intelligence Hub")
    st.markdown(
        "<p style='color:#94A3B8;font-size:1.05rem;margin-top:-0.5rem;'>"
        "Personalized AI companion &amp; synchronized daily routine schedule."
        "</p>",
        unsafe_allow_html=True,
    )

    api_key_set = bool(get_groq_api_key())
    model_id = get_groq_model_id()
    now_local = get_current_local_datetime(tz_name)
    now_date_str = now_local.strftime("%A, %B %d, %Y")
    now_time_str = now_local.strftime("%I:%M %p")

    groq_badge_cls = "aidaxis-badge-teal" if api_key_set else "aidaxis-badge-amber"
    groq_label = f"&#9679; Groq: {_safe(model_id)}" if api_key_set else "&#9888; Groq Key Not Configured"

    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown(
            f"""
            <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:1rem;">
                <span class="aidaxis-badge aidaxis-badge-violet">Patient: {_safe(patient_id)}</span>
                <span class="aidaxis-badge {groq_badge_cls}">{groq_label}</span>
                <span class="aidaxis-badge aidaxis-badge-violet">Timezone: {_safe(tz_name)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_h2:
        st.markdown(
            f"""
            <div style="text-align:right;color:#94A3B8;font-size:0.85rem;margin-top:0.25rem;">
                🕒 <strong style="color:#F8FAFC;">{_safe(now_time_str)}</strong>
                &nbsp;|&nbsp; {_safe(now_date_str)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_chat, col_schedule = st.columns([1, 1], gap="medium")

    # =========================================================
    # LEFT PANEL: MEMORY COMPANION
    # =========================================================
    with col_chat:
        st.markdown(
            """
            <div class="aidaxis-card aidaxis-card-accent"
                 style="padding:1rem 1.25rem;margin-bottom:0.75rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h4 style="margin:0;color:#F8FAFC;">💬 Memory Companion</h4>
                        <div style="font-size:0.8rem;color:#94A3B8;">
                            Natural-language scheduling &amp; memory assistance
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='font-size:0.75rem;color:#64748B;margin-bottom:0.25rem;'>SUGGESTED PROMPTS:</div>",
            unsafe_allow_html=True,
        )
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("📋 What do I have today?", use_container_width=True, key="btn_q_today"):
                handle_chat_input("What do I have scheduled for today?", patient_id, repository, tz_name)
        with q2:
            if st.button("🌅 What is tomorrow?", use_container_width=True, key="btn_q_tomorrow"):
                handle_chat_input("What do I have scheduled tomorrow?", patient_id, repository, tz_name)
        with q3:
            if st.button("✅ Completed tasks?", use_container_width=True, key="btn_q_completed"):
                handle_chat_input("What have I completed today?", patient_id, repository, tz_name)

        chat_container = st.container(height=480)
        with chat_container:
            for msg in st.session_state["chat_messages"]:
                avatar = "🤖" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

        user_prompt = st.chat_input(
            "Type an appointment, question, or change (e.g. 'Add dentist visit on Friday at 3 PM')..."
        )
        if user_prompt:
            handle_chat_input(user_prompt, patient_id, repository, tz_name)

        c_clear, _ = st.columns([1, 2])
        with c_clear:
            if st.button("Clear Conversation", use_container_width=True, key="btn_clear_chat"):
                st.session_state["chat_messages"] = [
                    {
                        "role": "assistant",
                        "content": (
                            "Conversation cleared. Your scheduled activities remain safely stored. "
                            "How can I help?"
                        ),
                    }
                ]
                st.rerun()

    # =========================================================
    # RIGHT PANEL: MY SCHEDULE
    # =========================================================
    with col_schedule:
        render_my_schedule_panel(patient_id, repository, tz_name)


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def handle_chat_input(
    user_prompt: str,
    patient_id: str,
    repository: EventRepository,
    tz_name: str,
):
    """Processes a chat prompt with Groq and reloads to show the updated schedule."""
    st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})

    with st.spinner("Memory Companion is thinking..."):
        reply, updated_history, action = run_memory_companion_chat(
            user_message=user_prompt,
            conversation_history=st.session_state["chat_messages"][:-1],
            user_id=patient_id,
            repository=repository,
            tz_name=tz_name,
        )

    st.session_state["chat_messages"] = updated_history
    st.rerun()


# ---------------------------------------------------------------------------
# Right panel: My Schedule
# ---------------------------------------------------------------------------

def render_my_schedule_panel(
    patient_id: str,
    repository: EventRepository,
    tz_name: str,
):
    """Renders the structured visual daily routine and interactive event management."""
    now_local = get_current_local_datetime(tz_name)
    today_iso = now_local.date().strftime("%Y-%m-%d")
    tomorrow_iso = (now_local.date() + timedelta(days=1)).strftime("%Y-%m-%d")

    st.markdown(
        """
        <div class="aidaxis-card aidaxis-card-teal"
             style="padding:1rem 1.25rem;margin-bottom:0.75rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <h4 style="margin:0;color:#F8FAFC;">📅 My Schedule</h4>
                    <div style="font-size:0.8rem;color:#94A3B8;">
                        Real-time synchronized activities &amp; appointments
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_today, tab_tomorrow, tab_upcoming, tab_completed, tab_all = st.tabs(
        ["📅 Today", "🌅 Tomorrow", "⏳ Upcoming", "✅ Completed", "📋 All"]
    )

    with tab_today:
        events = repository.get_events(patient_id, event_date=today_iso)
        render_event_list(events, "today", patient_id, repository)

    with tab_tomorrow:
        events = repository.get_events(patient_id, event_date=tomorrow_iso)
        render_event_list(events, "tomorrow", patient_id, repository)

    with tab_upcoming:
        events = repository.get_events(patient_id, start_date=today_iso, status="Upcoming")
        render_event_list(events, "upcoming", patient_id, repository)

    with tab_completed:
        events = repository.get_events(patient_id, status="Completed")
        render_event_list(events, "completed", patient_id, repository)

    with tab_all:
        events = repository.get_events(patient_id)
        render_event_list(events, "all", patient_id, repository)

    with st.expander("➕ Manually Add an Activity to Schedule"):
        render_manual_add_form(patient_id, repository, tz_name)


# ---------------------------------------------------------------------------
# Event list renderer
# ---------------------------------------------------------------------------

def render_event_list(
    events: List[Dict[str, Any]],
    category_name: str,
    patient_id: str,
    repository: EventRepository,
):
    """
    Renders event cards with interactive controls.

    All widget keys are prefixed with ``category_name`` so the same event
    appearing in multiple tabs (e.g. Today *and* Upcoming) never produces a
    ``StreamlitDuplicateElementKey`` error.
    """
    if not events:
        st.markdown(
            f"""
            <div class="aidaxis-card"
                 style="text-align:center;padding:2rem 1rem;margin-top:0.5rem;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">🏖️</div>
                <div style="color:#F8FAFC;font-weight:600;">
                    No {_safe(category_name)} activities scheduled
                </div>
                <div style="font-size:0.85rem;color:#94A3B8;margin-top:0.25rem;">
                    Use the Memory Companion chat or the form below to add one.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    editing_id = st.session_state.get("editing_event_id")

    for ev in events:
        eid = ev["event_id"]
        # Unique key prefix — prevents collisions when same event is in multiple tabs
        kp = f"{category_name}_{eid}"

        status = ev.get("status", "Upcoming")
        is_completed = status == "Completed"
        is_cancelled = status == "Cancelled"

        if editing_id == eid:
            render_inline_edit_form(ev, patient_id, repository, category_name)
            continue

        # Determine badge & card accent based on status
        if is_completed:
            badge_cls = "aidaxis-badge-teal"
            accent_cls = "aidaxis-card-teal"
        elif status == "Upcoming":
            badge_cls = "aidaxis-badge-violet"
            accent_cls = "aidaxis-card-accent"
        else:
            badge_cls = "aidaxis-badge-amber"
            accent_cls = ""

        opacity_style = "opacity:0.75;" if is_cancelled else ""
        title_deco = "line-through" if is_completed else "none"

        f_date = format_friendly_date(ev["event_date"])
        f_time = format_friendly_time(ev["start_time"])
        end_time_str = (
            f" – {format_friendly_time(ev['end_time'])}" if ev.get("end_time") else ""
        )

        # Build optional rows as separate strings — avoids HTML leaking from DB data
        # into the outer f-string via Python's conditional expression.
        location_html = (
            f'<div style="font-size:0.8rem;color:#64748B;margin-top:0.15rem;">'
            f'📍 {_safe(ev["location"])}</div>'
            if ev.get("location")
            else ""
        )
        notes_html = (
            f'<div style="font-size:0.8rem;color:#A78BFA;margin-top:0.15rem;">'
            f'📝 {_safe(ev["notes"])}</div>'
            if ev.get("notes")
            else ""
        )

        # Build card HTML via concatenation — avoids the Markdown 4-space code-block
        # rule that fires when multi-line triple-quoted f-strings have deep indentation
        # around interpolated variables like {location_html} / {notes_html}.
        card_html = (
            f'<div class="aidaxis-card {accent_cls}"'
            f' style="margin-bottom:0.65rem;padding:0.9rem 1.1rem;{opacity_style}">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-size:1.05rem;font-weight:600;color:#F8FAFC;'
            f'text-decoration:{title_deco};">'
            f'{_safe(ev["title"])}</div>'
            f'<div style="font-size:0.85rem;color:#94A3B8;margin:0.2rem 0;">'
            f'\U0001f552 <strong style="color:#CBD5E1;">{f_time}{end_time_str}</strong>'
            f'&nbsp;|&nbsp; \U0001f4c5 {f_date}</div>'
            + location_html
            + notes_html
            + f'</div>'
            f'<span class="aidaxis-badge {badge_cls}"'
            f' style="margin-left:0.75rem;white-space:nowrap;">{_safe(status)}</span>'
            f'</div></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # ── Action buttons ──────────────────────────────────────────────────
        c_act1, c_act2, c_act3, _ = st.columns([1, 1, 1, 2])
        with c_act1:
            if not is_completed and not is_cancelled:
                if st.button("✅ Done", key=f"btn_done_{kp}", use_container_width=True):
                    repository.mark_event_completed(eid, patient_id)
                    st.rerun()
        with c_act2:
            if not is_cancelled:
                if st.button("✏️ Edit", key=f"btn_edit_{kp}", use_container_width=True):
                    st.session_state["editing_event_id"] = eid
                    st.rerun()
        with c_act3:
            if not is_cancelled and not is_completed:
                if st.button("🗑️ Remove", key=f"btn_del_{kp}", use_container_width=True):
                    st.session_state["pending_cancel_event_id"] = eid
                    st.rerun()

        # ── Inline cancellation confirmation ────────────────────────────────
        if st.session_state.get("pending_cancel_event_id") == eid:
            st.markdown(
                f"""
                <div style="background:rgba(239,68,68,0.12);
                            border:1px solid rgba(239,68,68,0.35);
                            border-radius:10px;
                            padding:0.65rem 0.9rem;
                            margin-bottom:0.4rem;">
                    <div style="color:#FCA5A5;font-size:0.9rem;font-weight:600;
                                margin-bottom:0.3rem;">
                        ⚠️ Remove &quot;{_safe(ev['title'])}&quot;?
                    </div>
                    <div style="color:#94A3B8;font-size:0.8rem;">
                        This will mark the activity as cancelled.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button(
                    "Yes, Remove",
                    key=f"conf_yes_{kp}",
                    type="primary",
                    use_container_width=True,
                ):
                    repository.cancel_event(eid, patient_id)
                    st.session_state["pending_cancel_event_id"] = None
                    st.rerun()
            with c_no:
                if st.button("No, Keep It", key=f"conf_no_{kp}", use_container_width=True):
                    st.session_state["pending_cancel_event_id"] = None
                    st.rerun()


# ---------------------------------------------------------------------------
# Inline edit form
# ---------------------------------------------------------------------------

def render_inline_edit_form(
    event: Dict[str, Any],
    patient_id: str,
    repository: EventRepository,
    category_name: str = "",
):
    """
    Inline edit form for modifying event details.
    ``category_name`` is included in keys to keep them unique across tabs.
    """
    eid = event["event_id"]
    kp = f"{category_name}_{eid}" if category_name else str(eid)

    st.markdown(
        f"""
        <div class="aidaxis-card aidaxis-card-accent"
             style="padding:1rem 1.25rem;margin-bottom:0.5rem;">
            <div style="font-weight:600;color:#F8FAFC;">
                ✏️ Edit: {_safe(event['title'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_title = st.text_input("Title:", value=event["title"], key=f"edit_title_{kp}")
    col1, col2 = st.columns(2)
    with col1:
        new_date = st.text_input(
            "Date (YYYY-MM-DD):", value=event["event_date"], key=f"edit_date_{kp}"
        )
    with col2:
        new_time = st.text_input(
            "Start Time:", value=event["start_time"], key=f"edit_time_{kp}"
        )

    new_loc = st.text_input(
        "Location:", value=event.get("location") or "", key=f"edit_loc_{kp}"
    )
    new_notes = st.text_input(
        "Notes:", value=event.get("notes") or "", key=f"edit_notes_{kp}"
    )

    c_save, c_cancel = st.columns(2)
    with c_save:
        if st.button(
            "💾 Save Changes",
            type="primary",
            key=f"btn_save_{kp}",
            use_container_width=True,
        ):
            repository.update_event(
                event_id=eid,
                user_id=patient_id,
                updates={
                    "title": new_title,
                    "event_date": new_date,
                    "start_time": new_time,
                    "location": new_loc,
                    "notes": new_notes,
                },
            )
            st.session_state["editing_event_id"] = None
            st.rerun()
    with c_cancel:
        if st.button(
            "✖ Discard Changes", key=f"btn_cancel_edit_{kp}", use_container_width=True
        ):
            st.session_state["editing_event_id"] = None
            st.rerun()


# ---------------------------------------------------------------------------
# Manual add form
# ---------------------------------------------------------------------------

def render_manual_add_form(
    patient_id: str,
    repository: EventRepository,
    tz_name: str,
):
    """Form for manual event creation directly in My Schedule."""
    now_local = get_current_local_datetime(tz_name)
    def_date = now_local.date()

    with st.form("manual_add_event_form"):
        title = st.text_input(
            "Activity Title *",
            placeholder="e.g., Doctor Visit / Morning Walk / Take Donepezil",
        )
        c1, c2 = st.columns(2)
        with c1:
            ev_date = st.date_input("Date *", value=def_date)
        with c2:
            ev_time = st.text_input(
                "Time *", value="10:00 AM", placeholder="e.g., 10:00 AM or 14:30"
            )

        location = st.text_input(
            "Location (Optional)", placeholder="e.g., General Hospital, Room 204"
        )
        notes = st.text_area(
            "Notes / Instructions (Optional)",
            placeholder="e.g., Bring past medical records",
            height=70,
        )

        submitted = st.form_submit_button("➕ Save Event to Schedule", type="primary")
        if submitted:
            if not title.strip():
                st.error("Please enter a title for the activity.")
            else:
                repository.create_event(
                    {
                        "user_id": patient_id,
                        "title": title.strip(),
                        "event_date": ev_date.strftime("%Y-%m-%d"),
                        "start_time": ev_time.strip(),
                        "timezone": tz_name,
                        "location": location.strip(),
                        "notes": notes.strip(),
                        "status": "Upcoming",
                    }
                )
                st.success(f"Event '{title}' saved successfully!")
                st.rerun()
