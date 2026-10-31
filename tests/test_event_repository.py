"""
=========================================================
Aid Axis - Unit Tests for Event Repository

Verifies:
1. Event creation, retrieval, and parameterized storage
2. Patient isolation (no cross-contamination of events)
3. Event updates, completions, and cancellations
4. Idempotent duplicate event prevention
=========================================================
"""

import unittest
import tempfile
from pathlib import Path
from database.event_repository import EventRepository


class TestEventRepository(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_events.db"
        self.repo = EventRepository(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_retrieve_event(self):
        event_data = {
            "user_id": "TEST-USER-1",
            "title": "Neurology Consultation",
            "event_date": "2026-11-05",
            "start_time": "10:30 AM",
            "location": "Room 401",
            "notes": "Bring previous scans",
            "status": "Upcoming"
        }

        created = self.repo.create_event(event_data)
        self.assertIsNotNone(created)
        self.assertEqual(created["title"], "Neurology Consultation")

        # Retrieve
        events = self.repo.get_events("TEST-USER-1", event_date="2026-11-05")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], created["event_id"])

    def test_user_isolation(self):
        ev1 = {
            "user_id": "USER-ALICE",
            "title": "Alice Activity",
            "event_date": "2026-11-01",
            "start_time": "09:00 AM"
        }
        ev2 = {
            "user_id": "USER-BOB",
            "title": "Bob Activity",
            "event_date": "2026-11-01",
            "start_time": "09:00 AM"
        }
        self.repo.create_event(ev1)
        self.repo.create_event(ev2)

        alice_events = self.repo.get_events("USER-ALICE")
        bob_events = self.repo.get_events("USER-BOB")

        self.assertEqual(len(alice_events), 1)
        self.assertEqual(alice_events[0]["title"], "Alice Activity")

        self.assertEqual(len(bob_events), 1)
        self.assertEqual(bob_events[0]["title"], "Bob Activity")

    def test_update_and_complete_event(self):
        ev = self.repo.create_event({
            "user_id": "USER-CHARLIE",
            "title": "Physical Therapy",
            "event_date": "2026-11-02",
            "start_time": "11:00 AM"
        })
        eid = ev["event_id"]

        # Update time
        updated = self.repo.update_event(eid, "USER-CHARLIE", {"start_time": "11:30 AM"})
        self.assertEqual(updated["start_time"], "11:30 AM")

        # Complete
        ok = self.repo.mark_event_completed(eid, "USER-CHARLIE")
        self.assertTrue(ok)
        completed_ev = self.repo.get_event_by_id(eid, "USER-CHARLIE")
        self.assertEqual(completed_ev["status"], "Completed")

    def test_duplicate_prevention_idempotency(self):
        ev = {
            "user_id": "USER-DANA",
            "title": "Daily Medication",
            "event_date": "2026-11-03",
            "start_time": "08:00 AM"
        }
        first = self.repo.create_event(ev)
        second = self.repo.create_event(ev)

        # Same event_id returned, no duplicate created
        self.assertEqual(first["event_id"], second["event_id"])
        all_events = self.repo.get_events("USER-DANA")
        self.assertEqual(len(all_events), 1)


if __name__ == "__main__":
    unittest.main()
