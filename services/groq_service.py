"""
=========================================================
Aid Axis - Groq Service (Memory Intelligence Hub)

Integrates Groq LLM API with official Python SDK, implementing
controlled tool-calling for natural-language scheduling, secure
credential resolution, and clinical conversation safeguards.
=========================================================
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import groq
from groq import (
    Groq,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError
)

from database.event_repository import EventRepository
from services.datetime_service import (
    get_current_local_datetime,
    parse_relative_date_phrase,
    normalize_time_input,
    format_friendly_date,
    format_friendly_time
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]


def get_groq_api_key() -> Optional[str]:
    """
    Retrieves Groq API key with precedence:
    1. Streamlit secrets (.streamlit/secrets.toml)
    2. Environment variable GROQ_API_KEY
    """
    # 1. Check Streamlit secrets
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass

    # 2. Check environment variable
    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return env_key.strip()

    return None


def get_groq_model_id() -> str:
    """
    Retrieves configured model ID with precedence:
    1. Streamlit secrets
    2. Environment variable
    3. Default: openai/gpt-oss-20b
    """
    try:
        if "GROQ_MODEL" in st.secrets and st.secrets["GROQ_MODEL"]:
            return str(st.secrets["GROQ_MODEL"]).strip()
    except Exception:
        pass

    env_model = os.getenv("GROQ_MODEL")
    if env_model:
        return env_model.strip()

    return DEFAULT_MODEL


def get_groq_client() -> Tuple[Optional[Groq], Optional[str]]:
    """
    Instantiates Groq client. Returns (client, error_message).
    """
    api_key = get_groq_api_key()
    if not api_key:
        return None, "GROQ_API_KEY is not configured in .streamlit/secrets.toml or environment variables."

    try:
        client = Groq(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Failed to initialize Groq client: {str(e)}"


# =========================================================
# Tool Definitions for Groq Function Calling
# =========================================================
SCHEDULE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Saves a new activity or appointment to the patient's schedule. Do not call this if the start time is completely missing; instead ask the user what time they prefer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short, clear title of the event (e.g., 'Doctor Appointment', 'Morning Walk', 'Take Medication')."
                    },
                    "event_date": {
                        "type": "string",
                        "description": "Date of the event in YYYY-MM-DD format or relative phrase (e.g., 'today', 'tomorrow', 'Friday', 'next Monday')."
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Starting time in 12-hour AM/PM format (e.g., '10:00 AM', '02:30 PM') or 24-hour format ('14:30')."
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Optional end time (e.g., '11:00 AM')."
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional location or room."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional preparation notes, instructions, or doctor name."
                    }
                },
                "required": ["title", "event_date", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Retrieves the patient's actual recorded events from the database. Call this whenever the user asks what they have scheduled or completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_filter": {
                        "type": "string",
                        "description": "Filter by date: 'today', 'tomorrow', 'upcoming', 'past', 'all', or a specific date in YYYY-MM-DD format."
                    },
                    "status_filter": {
                        "type": "string",
                        "enum": ["Upcoming", "Completed", "Cancelled", "all"],
                        "description": "Filter by event status. Default is 'all' or 'Upcoming'."
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Optional keyword search in event title, notes, or location."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": "Updates an existing scheduled event (e.g. moving a meeting time, changing date or location).",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_title": {
                        "type": "string",
                        "description": "The title or keyword of the event to modify (e.g. 'meeting', 'doctor')."
                    },
                    "event_id": {
                        "type": "string",
                        "description": "The unique event_id if known."
                    },
                    "new_title": {
                        "type": "string",
                        "description": "New title for the event, if changing."
                    },
                    "new_date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD or relative format, if changing."
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "New start time (e.g. '11:00 AM'), if changing."
                    },
                    "new_location": {
                        "type": "string",
                        "description": "New location, if changing."
                    },
                    "new_notes": {
                        "type": "string",
                        "description": "New notes, if changing."
                    }
                },
                "required": ["search_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_event_completed",
            "description": "Marks an event as 'Completed' once the user finishes it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_title": {
                        "type": "string",
                        "description": "The title or keyword of the event to mark completed (e.g. 'morning walk')."
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Specific event ID if known."
                    }
                },
                "required": ["search_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_event",
            "description": "Cancels an event. If user explicitly confirms cancellation, sets status to 'Cancelled'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_title": {
                        "type": "string",
                        "description": "The title or keyword of the event to cancel."
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Specific event ID if known."
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "True if user stated confirmation like 'yes cancel it' or 'please cancel'."
                    }
                },
                "required": ["search_title"]
            }
        }
    }
]


# =========================================================
# Tool Execution Dispatcher
# =========================================================
def execute_backend_tool(
    tool_name: str,
    args: Dict[str, Any],
    user_id: str,
    repository: EventRepository,
    tz_name: str = "Asia/Kolkata"
) -> Dict[str, Any]:
    """
    Validates arguments and executes the requested database operation.
    Returns structured results for Groq to synthesize into conversation.
    """
    logger.info("Executing tool %s for user %s with args: %s", tool_name, user_id, args)

    try:
        if tool_name == "create_event":
            title = args.get("title", "").strip()
            raw_date = args.get("event_date", "").strip()
            raw_time = args.get("start_time", "").strip()

            if not title:
                return {"success": False, "error": "Event title is missing. Please provide a title."}

            if not raw_time:
                return {"success": False, "error": "Start time is missing. Please ask user what time the event is."}

            # Resolve relative date
            resolved_date, _ = parse_relative_date_phrase(raw_date, tz_name)
            if not resolved_date:
                return {"success": False, "error": f"Could not determine date from '{raw_date}'."}

            normalized_time = normalize_time_input(raw_time) or raw_time
            norm_end = normalize_time_input(args.get("end_time")) if args.get("end_time") else None

            event_record = {
                "user_id": user_id,
                "title": title,
                "event_date": resolved_date,
                "start_time": normalized_time,
                "end_time": norm_end,
                "timezone": tz_name,
                "location": args.get("location"),
                "notes": args.get("notes"),
                "status": "Upcoming"
            }

            saved = repository.create_event(event_record)
            return {
                "success": True,
                "action": "created",
                "event": saved,
                "formatted_date": format_friendly_date(saved["event_date"]),
                "formatted_time": format_friendly_time(saved["start_time"])
            }

        elif tool_name == "get_events":
            date_filter = str(args.get("date_filter", "all")).lower().strip()
            status_filter = args.get("status_filter")
            search_query = args.get("search_query")
            now_local = get_current_local_datetime(tz_name)
            today_str = now_local.date().strftime("%Y-%m-%d")

            events = []
            if date_filter == "today":
                events = repository.get_events(user_id, event_date=today_str, status=status_filter, search_query=search_query)
            elif date_filter == "tomorrow":
                from datetime import timedelta
                tomorrow_str = (now_local.date() + timedelta(days=1)).strftime("%Y-%m-%d")
                events = repository.get_events(user_id, event_date=tomorrow_str, status=status_filter, search_query=search_query)
            elif date_filter == "upcoming":
                events = repository.get_events(user_id, start_date=today_str, status=status_filter or "Upcoming", search_query=search_query)
            elif date_filter == "past":
                events = repository.get_events(user_id, end_date=today_str, status=status_filter, search_query=search_query)
            elif len(date_filter) == 10 and date_filter.count("-") == 2:
                # Direct ISO date
                events = repository.get_events(user_id, event_date=date_filter, status=status_filter, search_query=search_query)
            else:
                resolved_d, _ = parse_relative_date_phrase(date_filter, tz_name)
                if resolved_d:
                    events = repository.get_events(user_id, event_date=resolved_d, status=status_filter, search_query=search_query)
                else:
                    events = repository.get_events(user_id, status=status_filter, search_query=search_query)

            # Format list for LLM context
            formatted_list = []
            for ev in events:
                formatted_list.append({
                    "event_id": ev["event_id"],
                    "title": ev["title"],
                    "date": format_friendly_date(ev["event_date"]),
                    "raw_date": ev["event_date"],
                    "start_time": format_friendly_time(ev["start_time"]),
                    "status": ev["status"],
                    "location": ev.get("location") or "Not specified",
                    "notes": ev.get("notes") or ""
                })

            return {
                "success": True,
                "count": len(formatted_list),
                "events": formatted_list
            }

        elif tool_name == "update_event":
            search_title = args.get("search_title", "")
            event_id = args.get("event_id")

            target_event = None
            if event_id:
                target_event = repository.get_event_by_id(event_id, user_id)
            elif search_title:
                matches = repository.find_event_by_title_fuzzy(user_id, search_title)
                if not matches:
                    return {"success": False, "error": f"No scheduled event found matching '{search_title}'."}
                if len(matches) > 1:
                    match_summaries = [f"'{m['title']}' on {m['event_date']} at {m['start_time']} (ID: {m['event_id']})" for m in matches[:3]]
                    return {
                        "success": False,
                        "ambiguous": True,
                        "error": f"Multiple events match '{search_title}'. Please specify which one: {'; '.join(match_summaries)}"
                    }
                target_event = matches[0]

            if not target_event:
                return {"success": False, "error": "Target event could not be found."}

            updates = {}
            if args.get("new_title"):
                updates["title"] = args["new_title"].strip()
            if args.get("new_date"):
                resolved_d, _ = parse_relative_date_phrase(args["new_date"], tz_name)
                if resolved_d:
                    updates["event_date"] = resolved_d
            if args.get("new_start_time"):
                updates["start_time"] = normalize_time_input(args["new_start_time"]) or args["new_start_time"]
            if args.get("new_location"):
                updates["location"] = args["new_location"].strip()
            if args.get("new_notes"):
                updates["notes"] = args["new_notes"].strip()

            updated_event = repository.update_event(target_event["event_id"], user_id, updates)
            return {
                "success": True,
                "action": "updated",
                "event": updated_event,
                "formatted_date": format_friendly_date(updated_event["event_date"]),
                "formatted_time": format_friendly_time(updated_event["start_time"])
            }

        elif tool_name == "mark_event_completed":
            search_title = args.get("search_title", "")
            event_id = args.get("event_id")

            target_id = event_id
            if not target_id and search_title:
                matches = repository.find_event_by_title_fuzzy(user_id, search_title)
                if not matches:
                    return {"success": False, "error": f"No active event found matching '{search_title}'."}
                target_id = matches[0]["event_id"]

            if not target_id:
                return {"success": False, "error": "Could not identify which event to complete."}

            ok = repository.mark_event_completed(target_id, user_id)
            ev = repository.get_event_by_id(target_id, user_id)
            return {
                "success": ok,
                "action": "completed",
                "title": ev["title"] if ev else "Event"
            }

        elif tool_name == "cancel_event":
            search_title = args.get("search_title", "")
            event_id = args.get("event_id")
            confirmed = bool(args.get("confirmed", False))

            matches = []
            if event_id:
                ev = repository.get_event_by_id(event_id, user_id)
                if ev:
                    matches = [ev]
            elif search_title:
                matches = repository.find_event_by_title_fuzzy(user_id, search_title)

            if not matches:
                return {"success": False, "error": f"No active event found matching '{search_title}'."}

            if len(matches) > 1:
                summaries = [f"'{m['title']}' on {m['event_date']}" for m in matches[:3]]
                return {"success": False, "ambiguous": True, "error": f"Multiple events match '{search_title}'. Which one do you mean? {', '.join(summaries)}"}

            target = matches[0]
            if not confirmed:
                return {
                    "success": False,
                    "needs_confirmation": True,
                    "event_id": target["event_id"],
                    "title": target["title"],
                    "date": format_friendly_date(target["event_date"]),
                    "time": format_friendly_time(target["start_time"]),
                    "prompt": f"Are you sure you want to cancel '{target['title']}' on {format_friendly_date(target['event_date'])} at {format_friendly_time(target['start_time'])}?"
                }

            ok = repository.cancel_event(target["event_id"], user_id)
            return {
                "success": ok,
                "action": "cancelled",
                "title": target["title"]
            }

        else:
            return {"success": False, "error": f"Unsupported tool operation: {tool_name}"}

    except Exception as e:
        logger.exception("Error executing tool %s", tool_name)
        return {"success": False, "error": f"Database operation failed: {str(e)}"}


# =========================================================
# Conversational Groq Agent Loop
# =========================================================
def run_memory_companion_chat(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    user_id: str,
    repository: EventRepository,
    tz_name: str = "Asia/Kolkata"
) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Executes Groq conversational tool-calling loop:
    1. Prepares system instructions with current date/time context.
    2. Sends messages to Groq.
    3. Handles requested function calls with strict backend validation.
    4. Obtains real database records and returns them to Groq.
    5. Returns (assistant_reply, updated_history, action_performed).
    """
    client, err = get_groq_client()
    if not client:
        return (
            f"⚠️ **Memory Companion Configuration Alert:** {err}\n\n"
            "Please check that `GROQ_API_KEY` is specified in `.streamlit/secrets.toml`.",
            conversation_history,
            None
        )

    model_id = get_groq_model_id()
    now_local = get_current_local_datetime(tz_name)
    current_date_str = now_local.strftime("%Y-%m-%d")
    current_time_str = now_local.strftime("%I:%M %p")
    day_name = now_local.strftime("%A")

    system_prompt = f"""You are the Aid Axis Memory Companion — a warm, clear, and reassuring AI personal scheduling assistant designed for cognitive health and memory care.

TEMPORAL CONTEXT:
- Today's Date: {current_date_str} ({day_name})
- Current Local Time: {current_time_str}
- Local Timezone: {tz_name}
- Active Patient Identifier: {user_id}

CLINICAL & SCHEDULING GUIDELINES:
1. Speak in a gentle, clear, supportive, and accessible tone suitable for patients and caregivers.
2. You have real database tools: create_event, get_events, update_event, mark_event_completed, cancel_event.
3. ALWAYS check the database via `get_events` when the user asks what they have scheduled or completed today, tomorrow, or in the future. Never fabricate or hallucinate events.
4. When adding an event:
   - If the user provides a title and time (e.g. "I have a doctor visit tomorrow at 10 AM"), call `create_event`.
   - If the user mentions an activity without a time (e.g. "I have a meeting tomorrow"), DO NOT guess or fabricate a time. Politely ask: "What time is your meeting scheduled for?"
5. When modifying or cancelling an event:
   - Identify the specific event. If multiple events match, ask for clarification.
   - For cancellations, verify confirmation.
6. Only confirm that an action succeeded after the database tool confirms it.
7. Keep responses concise, warm, and easy to read. Use bullet points for multiple schedule items.
"""

    # Assemble messages
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # Include recent history (limit to last 10 messages for context efficiency)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    last_action = None
    max_iterations = 4

    try:
        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                tools=SCHEDULE_TOOLS,
                tool_choice="auto",
                temperature=0.2
            )

            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls

            # If no tools requested, return final text reply
            if not tool_calls:
                final_text = response_msg.content or "I have processed your request."
                updated_history = conversation_history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": final_text}
                ]
                return final_text, updated_history, last_action

            # Model requested tool calling
            # Convert response_msg to dict format acceptable in conversation
            messages.append(response_msg)

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args_raw = tool_call.function.arguments

                try:
                    fn_args = json.loads(fn_args_raw)
                except Exception:
                    fn_args = {}

                # Execute backend tool securely
                tool_result = execute_backend_tool(
                    tool_name=fn_name,
                    args=fn_args,
                    user_id=user_id,
                    repository=repository,
                    tz_name=tz_name
                )
                last_action = {"tool": fn_name, "args": fn_args, "result": tool_result}

                # Feed result back to model
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result)
                })

        # Fallback if iterations exceed limit
        return (
            "I checked your request and updated your schedule. Please inspect My Schedule on the right panel.",
            conversation_history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": "Schedule updated."}],
            last_action
        )

    except AuthenticationError:
        err_msg = "⚠️ **Groq Authentication Error:** The provided API key is invalid or has expired. Please verify `.streamlit/secrets.toml`."
        return err_msg, conversation_history, None
    except RateLimitError:
        err_msg = "⚠️ **Groq Rate Limit Reached:** The current model quota has been temporarily exceeded. Please wait a few moments before sending another message."
        return err_msg, conversation_history, None
    except APIConnectionError:
        err_msg = "⚠️ **Network Connectivity Alert:** Unable to connect to the Groq API. Please verify your internet connection."
        return err_msg, conversation_history, None
    except APIStatusError as e:
        err_msg = f"⚠️ **Groq API Service Notice:** Service returned status {e.status_code}. Please try again shortly."
        return err_msg, conversation_history, None
    except Exception as e:
        logger.exception("Unexpected error in Groq Memory Companion loop")
        err_msg = "⚠️ An unexpected error occurred while communicating with the Memory Companion. Your saved schedule remains safe."
        return err_msg, conversation_history, None
