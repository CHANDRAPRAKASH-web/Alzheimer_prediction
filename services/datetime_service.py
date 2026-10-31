"""
=========================================================
Aid Axis - DateTime Service for Memory Intelligence Hub

Provides timezone-aware date parsing, relative phrase resolution
(e.g., today, tomorrow, next Friday), and user-friendly formatting
using Python datetime and zoneinfo.
=========================================================
"""

import re
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Dict, Any, Optional, Tuple


DEFAULT_TIMEZONE_STR = "Asia/Kolkata"


def get_configured_timezone(tz_name: Optional[str] = None) -> ZoneInfo:
    """
    Returns a ZoneInfo object, falling back safely to UTC if the timezone is invalid.
    """
    name = tz_name or DEFAULT_TIMEZONE_STR
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        try:
            return ZoneInfo(DEFAULT_TIMEZONE_STR)
        except Exception:
            return ZoneInfo("UTC")


def get_current_local_datetime(tz_name: Optional[str] = None) -> datetime:
    """
    Returns current datetime in the configured timezone.
    """
    tz = get_configured_timezone(tz_name)
    return datetime.now(tz)


def format_friendly_date(date_str: str) -> str:
    """
    Formats YYYY-MM-DD into a warm, readable representation.
    e.g. '2026-10-31' -> 'Saturday, Oct 31, 2026'
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%A, %b %d, %Y")
    except (ValueError, TypeError):
        return date_str


def format_friendly_time(time_str: str) -> str:
    """
    Formats 24h or arbitrary time string into consistent 12-hour AM/PM.
    e.g. '14:30' -> '02:30 PM', '10:00' -> '10:00 AM'
    """
    if not time_str:
        return ""
    t_str = time_str.strip()
    
    # Already 12h format
    if "AM" in t_str.upper() or "PM" in t_str.upper():
        return t_str

    # 24h format HH:MM or HH:MM:SS
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(t_str, fmt).time()
            return t.strftime("%I:%M %p")
        except ValueError:
            pass

    return t_str


def parse_relative_date_phrase(
    phrase: str,
    tz_name: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves phrases like 'today', 'tomorrow', 'next monday', 'this friday'
    into exact ISO date strings (YYYY-MM-DD).
    Returns (resolved_date_str, explanation).
    """
    if not phrase:
        return None, "Empty date expression"

    clean = phrase.strip().lower()
    now_local = get_current_local_datetime(tz_name)
    today = now_local.date()

    if clean in ("today", "tonight", "this morning", "this afternoon", "this evening"):
        return today.strftime("%Y-%m-%d"), "today"

    if clean == "tomorrow":
        tom = today + timedelta(days=1)
        return tom.strftime("%Y-%m-%d"), "tomorrow"

    if clean in ("day after tomorrow", "in two days", "in 2 days"):
        dat = today + timedelta(days=2)
        return dat.strftime("%Y-%m-%d"), "in 2 days"

    if clean == "yesterday":
        yest = today - timedelta(days=1)
        return yest.strftime("%Y-%m-%d"), "yesterday"

    # Day of week parsing: 'monday', 'next tuesday', 'this friday'
    weekday_map = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6
    }

    words = clean.split()
    target_weekday = None
    is_next = "next" in words

    for word in words:
        clean_w = word.replace(",", "")
        if clean_w in weekday_map:
            target_weekday = weekday_map[clean_w]
            break

    if target_weekday is not None:
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0 and is_next:
            days_ahead = 7
        elif days_ahead == 0 and not ("this" in words or "today" in words):
            days_ahead = 7
        elif is_next and days_ahead > 0:
            days_ahead += 7

        resolved = today + timedelta(days=days_ahead)
        return resolved.strftime("%Y-%m-%d"), f"resolved to {resolved.strftime('%A, %b %d')}"

    # Try direct ISO format (YYYY-MM-DD)
    try:
        dt = datetime.strptime(clean, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d"), "ISO formatted date"
    except ValueError:
        pass

    # Try common formats like MM/DD/YYYY or DD Month YYYY
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y", "%B %d", "%b %d"):
        try:
            dt = datetime.strptime(clean, fmt)
            # If year wasn't parsed (default 1900), set to current year
            if dt.year == 1900:
                dt = dt.replace(year=today.year)
                # If date is in the past, assume next year
                if dt.date() < today:
                    dt = dt.replace(year=today.year + 1)
            return dt.strftime("%Y-%m-%d"), "formatted date"
        except ValueError:
            pass

    return None, f"Could not determine date from '{phrase}'"


def normalize_time_input(time_str: str) -> Optional[str]:
    """
    Standardizes user/LLM time representations to clean 12-hour AM/PM format.
    Handles '10am', '10:00 AM', '14:30', '3 PM', '10' -> '10:00 AM'
    """
    if not time_str:
        return None

    clean = time_str.strip().upper()
    # Normalize '10AM' -> '10:00 AM', '3PM' -> '03:00 PM'
    match_simple = re.match(r"^(\d{1,2})\s*(AM|PM)$", clean)
    if match_simple:
        hr = int(match_simple.group(1))
        meridiem = match_simple.group(2)
        return f"{hr:02d}:00 {meridiem}"

    match_colon = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", clean)
    if match_colon:
        hr = int(match_colon.group(1))
        mn = int(match_colon.group(2))
        meridiem = match_colon.group(3)
        return f"{hr:02d}:{mn:02d} {meridiem}"

    # 24-hour time e.g. '14:30'
    match_24h = re.match(r"^(\d{1,2}):(\d{2})$", clean)
    if match_24h:
        hr = int(match_24h.group(1))
        mn = int(match_24h.group(2))
        if 0 <= hr <= 23 and 0 <= mn <= 59:
            t = time(hr, mn)
            return t.strftime("%I:%M %p")

    return None
