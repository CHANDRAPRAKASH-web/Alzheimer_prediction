"""
=========================================================
Aid Axis - Event Repository (Memory Intelligence Hub)

Handles persistent storage and retrieval of personal schedule
and memory assistance events. Employs parameterized queries,
strict user partitioning, and transaction safeguards.
=========================================================
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from database.connection import get_db_connection

logger = logging.getLogger(__name__)


class EventRepository:
    """
    Repository for managing daily schedule events and memory activities.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """
        Creates memory_events table and performance indexes if not present.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            timezone TEXT NOT NULL,
            location TEXT,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'Upcoming',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_events_user_date 
        ON memory_events(user_id, event_date, start_time);
        """
        with get_db_connection(self.db_path) as conn:
            conn.execute(create_table_sql)
            conn.execute(create_index_sql)

        self.seed_demo_events_if_needed()

    def seed_demo_events_if_needed(self) -> None:
        """
        Seeds sample events for demonstration patients if empty.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM memory_events WHERE user_id = 'PATIENT-001'")
                row = cursor.fetchone()
                if row and row["cnt"] > 0:
                    return
        except Exception:
            return

        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_str = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        demo_events = [
            # PATIENT-001 events
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-001",
                "title": "Morning Memory & Medication Routine",
                "event_date": today_str,
                "start_time": "08:30 AM",
                "end_time": "09:00 AM",
                "timezone": "Asia/Kolkata",
                "location": "Home - Kitchen",
                "notes": "Take morning vitamins and donepezil with water",
                "status": "Completed"
            },
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-001",
                "title": "Neurology Follow-up Consultation",
                "event_date": today_str,
                "start_time": "02:30 PM",
                "end_time": "03:30 PM",
                "timezone": "Asia/Kolkata",
                "location": "Aid Axis Cognitive Health Clinic, Room 302",
                "notes": "Discuss recent MRI report and cognitive questionnaire score",
                "status": "Upcoming"
            },
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-001",
                "title": "Physical Therapy & Balance Exercise",
                "event_date": tomorrow_str,
                "start_time": "10:00 AM",
                "end_time": "11:00 AM",
                "timezone": "Asia/Kolkata",
                "location": "Wellness Center",
                "notes": "Wear comfortable walking shoes",
                "status": "Upcoming"
            },
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-001",
                "title": "Community Cognitive Walking Club",
                "event_date": day_after_str,
                "start_time": "09:00 AM",
                "end_time": "10:15 AM",
                "timezone": "Asia/Kolkata",
                "location": "Botanical Gardens",
                "notes": "Accompanied by caregiver",
                "status": "Upcoming"
            },
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-001",
                "title": "Blood Pressure & Glucose Check",
                "event_date": yesterday_str,
                "start_time": "09:00 AM",
                "end_time": "09:30 AM",
                "timezone": "Asia/Kolkata",
                "location": "Home",
                "notes": "Readings: 124/82 mmHg, 98 mg/dL fasting",
                "status": "Completed"
            },
            # PATIENT-002 events
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-002",
                "title": "Speech & Language Therapy Session",
                "event_date": today_str,
                "start_time": "11:00 AM",
                "end_time": "12:00 PM",
                "timezone": "Asia/Kolkata",
                "location": "Telehealth Video Call",
                "notes": "Dr. Sarah Lin - Confrontation naming exercises",
                "status": "Upcoming"
            },
            {
                "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "user_id": "PATIENT-002",
                "title": "Cardiology Blood Work",
                "event_date": tomorrow_str,
                "start_time": "08:15 AM",
                "end_time": "09:00 AM",
                "timezone": "Asia/Kolkata",
                "location": "Metropolitan Diagnostic Lab",
                "notes": "Fasting required 8 hours prior",
                "status": "Upcoming"
            }
        ]

        for ev in demo_events:
            self.create_event(ev)

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new event with parameterized SQL insertion and validation.
        """
        user_id = str(event_data.get("user_id", "PATIENT-001")).strip()
        title = str(event_data.get("title", "")).strip()
        if not title:
            raise ValueError("Event title cannot be empty.")

        event_date = str(event_data.get("event_date", "")).strip()
        if not event_date:
            raise ValueError("Event date (YYYY-MM-DD) is required.")

        start_time = str(event_data.get("start_time", "09:00 AM")).strip()
        end_time = event_data.get("end_time")
        if end_time:
            end_time = str(end_time).strip()

        tz = str(event_data.get("timezone", "Asia/Kolkata")).strip()
        location = event_data.get("location")
        if location:
            location = str(location).strip()

        notes = event_data.get("notes")
        if notes:
            notes = str(notes).strip()

        status = event_data.get("status", "Upcoming")
        if status not in ("Upcoming", "Completed", "Cancelled"):
            status = "Upcoming"

        event_id = event_data.get("event_id") or f"EVT-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        insert_sql = """
        INSERT INTO memory_events (
            event_id, user_id, title, event_date, start_time,
            end_time, timezone, location, notes, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_db_connection(self.db_path) as conn:
            # Check duplicate idempotency
            chk = conn.execute(
                "SELECT event_id FROM memory_events WHERE user_id = ? AND title = ? AND event_date = ? AND start_time = ?",
                (user_id, title, event_date, start_time)
            ).fetchone()
            if chk:
                logger.info("Matching event already exists for %s: %s", user_id, chk["event_id"])
                return self.get_event_by_id(chk["event_id"], user_id)

            conn.execute(
                insert_sql,
                (
                    event_id, user_id, title, event_date, start_time,
                    end_time, tz, location, notes, status, now_iso, now_iso
                )
            )

        return self.get_event_by_id(event_id, user_id)

    def get_events(
        self,
        user_id: str,
        event_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves events for a patient with flexible date and status filtering.
        """
        query = "SELECT * FROM memory_events WHERE user_id = ?"
        params: List[Any] = [user_id]

        if event_date:
            query += " AND event_date = ?"
            params.append(event_date)
        elif start_date and end_date:
            query += " AND event_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND event_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND event_date <= ?"
            params.append(end_date)

        if status and status.lower() != "all":
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status)

        if search_query:
            query += " AND (title LIKE ? OR location LIKE ? OR notes LIKE ?)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard, wildcard])

        query += " ORDER BY event_date ASC, start_time ASC"

        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_event_by_id(self, event_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single event by event_id, enforcing user isolation when user_id is provided.
        """
        if user_id:
            query = "SELECT * FROM memory_events WHERE event_id = ? AND user_id = ?"
            params = (event_id, user_id)
        else:
            query = "SELECT * FROM memory_events WHERE event_id = ?"
            params = (event_id,)

        with get_db_connection(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def find_event_by_title_fuzzy(self, user_id: str, title_query: str) -> List[Dict[str, Any]]:
        """
        Searches upcoming or recent events matching a title fragment for conversational updates.
        """
        query = """
        SELECT * FROM memory_events 
        WHERE user_id = ? AND LOWER(title) LIKE LOWER(?) AND status != 'Cancelled'
        ORDER BY event_date ASC, start_time ASC
        """
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(query, (user_id, f"%{title_query}%")).fetchall()
            return [dict(r) for r in rows]

    def update_event(self, event_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates event fields safely with parameter binding.
        """
        existing = self.get_event_by_id(event_id, user_id)
        if not existing:
            return None

        allowed_fields = [
            "title", "event_date", "start_time", "end_time",
            "timezone", "location", "notes", "status"
        ]
        set_clauses = []
        params = []

        for field in allowed_fields:
            if field in updates and updates[field] is not None:
                set_clauses.append(f"{field} = ?")
                params.append(str(updates[field]).strip())

        if not set_clauses:
            return existing

        set_clauses.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())

        params.extend([event_id, user_id])
        update_sql = f"UPDATE memory_events SET {', '.join(set_clauses)} WHERE event_id = ? AND user_id = ?"

        with get_db_connection(self.db_path) as conn:
            conn.execute(update_sql, params)

        return self.get_event_by_id(event_id, user_id)

    def mark_event_completed(self, event_id: str, user_id: str) -> bool:
        """
        Transitions an event status to 'Completed'.
        """
        updated = self.update_event(event_id, user_id, {"status": "Completed"})
        return updated is not None and updated.get("status") == "Completed"

    def cancel_event(self, event_id: str, user_id: str) -> bool:
        """
        Transitions an event status to 'Cancelled'.
        """
        updated = self.update_event(event_id, user_id, {"status": "Cancelled"})
        return updated is not None and updated.get("status") == "Cancelled"

    def delete_event(self, event_id: str, user_id: str) -> bool:
        """
        Permanently removes an event record.
        """
        query = "DELETE FROM memory_events WHERE event_id = ? AND user_id = ?"
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, (event_id, user_id))
            return cursor.rowcount > 0
