"""
=========================================================
Aid Axis - Unit Tests for Progression Analytics

Verifies:
1. Consecutive comparison delta calculation
2. Domain-level variance tracking
3. Clinical narrative generation (neutral, cautious language)
4. Empty state and single assessment handling
=========================================================
"""

import unittest
from services.analytics_service import (
    compare_consecutive_assessments,
    generate_progression_narrative,
    compute_aggregate_overview
)


class TestProgressionAnalytics(unittest.TestCase):

    def test_compare_consecutive_assessments(self):
        prev = {
            "assessment_id": "P1",
            "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
            "assessment_date": "2026-09-01T10:00:00",
            "total_score": 25.0,
            "max_score": 30.0,
            "domain_scores": {
                "orientation_time": {"title": "Orientation: Time", "score": 4.0, "max_score": 5.0},
                "attention": {"title": "Attention & Calculation", "score": 3.0, "max_score": 5.0}
            }
        }
        latest = {
            "assessment_id": "P2",
            "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
            "assessment_date": "2026-09-15T10:00:00",
            "total_score": 27.0,
            "max_score": 30.0,
            "domain_scores": {
                "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0},
                "attention": {"title": "Attention & Calculation", "score": 4.0, "max_score": 5.0}
            }
        }

        comp = compare_consecutive_assessments(latest, prev)
        self.assertEqual(comp["score_diff"], 2.0)
        self.assertEqual(comp["abs_score_diff"], 2.0)
        self.assertEqual(comp["days_elapsed"], 14)
        self.assertEqual(comp["domain_deltas"]["orientation_time"]["delta"], 1.0)
        self.assertEqual(comp["domain_deltas"]["attention"]["delta"], 1.0)

    def test_narrative_generation_caution(self):
        comp = {
            "latest_score": 24.0,
            "previous_score": 26.0,
            "max_score": 30.0,
            "score_diff": -2.0,
            "days_elapsed": 30,
            "domain_deltas": {
                "attention": {"title": "Attention & Calculation", "delta": -2.0}
            }
        }
        narrative = generate_progression_narrative(comp, total_assessments=2)
        # Verify cautious descriptive tone and lack of unsupported claims
        self.assertIn("2.0 points lower", narrative)
        self.assertIn("over an interval of 30 days", narrative)
        self.assertIn("fatigue", narrative)
        self.assertNotIn("Alzheimer's disease has progressed", narrative)
        self.assertNotIn("severe dementia", narrative)

    def test_aggregate_overview_empty_states(self):
        # 0 assessments
        ov0 = compute_aggregate_overview([])
        self.assertFalse(ov0["has_data"])
        self.assertEqual(ov0["count"], 0)

        # 1 assessment
        ov1 = compute_aggregate_overview([{
            "total_score": 25.0,
            "assessment_date": "2026-10-01T10:00:00",
            "domain_scores": {"a": {}}
        }])
        self.assertTrue(ov1["has_data"])
        self.assertEqual(ov1["count"], 1)
        self.assertIsNone(ov1["prev_score"])
        self.assertIsNone(ov1["score_change"])


if __name__ == "__main__":
    unittest.main()
