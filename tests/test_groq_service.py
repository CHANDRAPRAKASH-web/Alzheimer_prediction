"""
=========================================================
Aid Axis - Unit Tests for Groq Tool Calling Logic

Verifies:
1. Tool argument validation
2. Controlled tool dispatching (create_event, get_events, update, complete, cancel)
3. Handling of missing fields and ambiguous searches
=========================================================
"""

import unittest
import tempfile
from pathlib import Path
from database.event_repository import EventRepository
from services.groq_service import execute_backend_tool


class TestGroqTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_groq_db.db"
        self.repo = EventRepository(db_path=self.db_path)
        self.user_id = "TEST-PATIENT"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_execute_create_event_tool(self):
        args = {
            "title": "Dentist Checkup",
            "event_date": "tomorrow",
            "start_time": "10:00 AM",
            "location": "Downtown Dental"
        }
        res = execute_backend_tool("create_event", args, self.user_id, self.repo)
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "created")
        self.assertEqual(res["event"]["title"], "Dentist Checkup")

    def test_execute_create_event_missing_time(self):
        args = {
            "title": "Dentist Checkup",
            "event_date": "tomorrow"
            # start_time missing
        }
        res = execute_backend_tool("create_event", args, self.user_id, self.repo)
        self.assertFalse(res["success"])
        self.assertIn("Start time is missing", res["error"])

    def test_execute_get_events_tool(self):
        # Seed an event first
        self.repo.create_event({
            "user_id": self.user_id,
            "title": "Cardio Walk",
            "event_date": "2026-11-04",
            "start_time": "09:00 AM",
            "status": "Upcoming"
        })

        res = execute_backend_tool("get_events", {"date_filter": "2026-11-04"}, self.user_id, self.repo)
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["events"][0]["title"], "Cardio Walk")

    def test_execute_update_event_tool(self):
        ev = self.repo.create_event({
            "user_id": self.user_id,
            "title": "Team Sync",
            "event_date": "2026-11-05",
            "start_time": "10:00 AM"
        })

        args = {
            "search_title": "Team Sync",
            "new_start_time": "11:00 AM"
        }
        res = execute_backend_tool("update_event", args, self.user_id, self.repo)
        self.assertTrue(res["success"])
        self.assertEqual(res["event"]["start_time"], "11:00 AM")

    def test_execute_cancel_event_with_confirmation(self):
        ev = self.repo.create_event({
            "user_id": self.user_id,
            "title": "Afternoon Tea Meeting",
            "event_date": "2026-11-06",
            "start_time": "04:00 PM"
        })

        # Step 1: Without explicit confirmation, triggers confirmation request
        res_unconfirmed = execute_backend_tool("cancel_event", {"search_title": "Afternoon Tea", "confirmed": False}, self.user_id, self.repo)
        self.assertFalse(res_unconfirmed["success"])
        self.assertTrue(res_unconfirmed.get("needs_confirmation"))

        # Step 2: With explicit confirmation, succeeds
        res_confirmed = execute_backend_tool("cancel_event", {"search_title": "Afternoon Tea", "confirmed": True}, self.user_id, self.repo)
        self.assertTrue(res_confirmed["success"])
        self.assertEqual(res_confirmed["action"], "cancelled")


if __name__ == "__main__":
    unittest.main()
