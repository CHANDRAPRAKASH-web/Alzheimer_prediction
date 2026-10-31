"""
=========================================================
Aid Axis - Unit Tests for Database Repository

Verifies:
1. SQLite connection and table creation
2. Parameterized insertion and non-overwrite policy
3. Idempotency & duplicate submission rejection
4. Chronological query ordering
5. Single record retrieval and count queries
=========================================================
"""

import unittest
import tempfile
import os
from pathlib import Path
from database.repository import AssessmentRepository


class TestAssessmentRepository(unittest.TestCase):

    def setUp(self):
        # Create a temporary database file for test isolation
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_aid_axis.db"
        self.repo = AssessmentRepository(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_assessment(self):
        record = {
            "assessment_id": "TEST-001",
            "patient_id": "PATIENT-ALPHA",
            "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
            "assessment_version": "v1.0-prototype",
            "assessment_date": "2026-10-01T10:00:00",
            "total_score": 26.0,
            "max_score": 30.0,
            "percentage_score": 86.7,
            "domain_scores": {"orientation_time": {"score": 5.0, "max_score": 5.0}},
            "responses": {"time_year": "2026"},
            "notes": "Test note"
        }

        success = self.repo.save_assessment(record)
        self.assertTrue(success)

        retrieved = self.repo.get_assessment_by_id("TEST-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["patient_id"], "PATIENT-ALPHA")
        self.assertEqual(retrieved["total_score"], 26.0)
        self.assertEqual(retrieved["domain_scores"]["orientation_time"]["score"], 5.0)

    def test_duplicate_prevention_idempotency(self):
        record = {
            "assessment_id": "TEST-DUP-01",
            "patient_id": "PATIENT-BETA",
            "assessment_date": "2026-10-02T12:00:00",
            "total_score": 28.0,
            "max_score": 30.0
        }

        # First insert succeeds
        first_try = self.repo.save_assessment(record)
        self.assertTrue(first_try)

        # Duplicate insert with identical assessment_id must return False
        second_try = self.repo.save_assessment(record)
        self.assertFalse(second_try)

        # Confirm count remains 1
        count = self.repo.count_assessments("PATIENT-BETA")
        self.assertEqual(count, 1)

    def test_chronological_ordering(self):
        r1 = {
            "assessment_id": "ORDER-1",
            "patient_id": "PATIENT-GAMMA",
            "assessment_date": "2026-09-01T10:00:00",
            "total_score": 24.0
        }
        r2 = {
            "assessment_id": "ORDER-2",
            "patient_id": "PATIENT-GAMMA",
            "assessment_date": "2026-10-01T10:00:00",
            "total_score": 27.0
        }

        # Save out of chronological order
        self.repo.save_assessment(r2)
        self.repo.save_assessment(r1)

        # Query ASC
        asc_list = self.repo.get_assessments_by_patient("PATIENT-GAMMA", order_asc=True)
        self.assertEqual(len(asc_list), 2)
        self.assertEqual(asc_list[0]["assessment_id"], "ORDER-1")
        self.assertEqual(asc_list[1]["assessment_id"], "ORDER-2")

        # Query latest
        latest = self.repo.get_latest_assessment("PATIENT-GAMMA")
        self.assertEqual(latest["assessment_id"], "ORDER-2")


if __name__ == "__main__":
    unittest.main()
