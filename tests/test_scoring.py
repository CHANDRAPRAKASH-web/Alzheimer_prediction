"""
=========================================================
Aid Axis - Unit Tests for Cognitive Scoring & Validation

Verifies:
1. Max score evaluation (30.0 / 30.0)
2. Zero score evaluation (0.0 / 30.0)
3. Domain sub-score accuracy
4. Serial 7s vs Backward spelling attention tasks
5. Step input validation logic
=========================================================
"""

import unittest
from datetime import datetime
from services.assessment_service import (
    calculate_assessment_score,
    validate_step,
    get_current_temporal_reference,
    MAX_ASSESSMENT_SCORE
)


class TestCognitiveScoring(unittest.TestCase):

    def setUp(self):
        self.temporal_ref = get_current_temporal_reference()

    def test_maximum_score_perfect_responses(self):
        """
        Verify that completely accurate responses achieve full 30.0 score.
        """
        perfect_responses = {
            "time_year": self.temporal_ref["year"],
            "time_season": self.temporal_ref["season"],
            "time_month": self.temporal_ref["month"],
            "time_date": self.temporal_ref["day_num"],
            "time_day": self.temporal_ref["day_name"],
            "place_country": "United States",
            "place_state": "California",
            "place_city": "San Francisco",
            "place_setting": "Clinic",
            "place_room": "Room 302",
            "registration_words": ["apple", "table", "penny"],
            "attention_mode": "serial7",
            "attention_serial7": ["93", "86", "79", "72", "65"],
            "recall_words": ["apple", "table", "penny"],
            "lang_naming_1": "Watch",
            "lang_naming_2": "Pen",
            "lang_repetition": "No ifs, ands, or buts",
            "lang_fluency": "Elephant",
            "comp_step_1": True,
            "comp_step_2": True,
            "comp_step_3": True,
            "visuo_pentagon": "Option B: Intersecting 5-sided pentagons with a 4-sided diamond intersection",
            "visuo_clock": "Option A: Hour hand pointing near 11, minute hand pointing exactly at 2"
        }

        result = calculate_assessment_score(perfect_responses)
        self.assertEqual(result["total_score"], MAX_ASSESSMENT_SCORE)
        self.assertEqual(result["percentage_score"], 100.0)
        self.assertEqual(result["domain_scores"]["orientation_time"]["score"], 5.0)
        self.assertEqual(result["domain_scores"]["orientation_place"]["score"], 5.0)
        self.assertEqual(result["domain_scores"]["registration"]["score"], 3.0)
        self.assertEqual(result["domain_scores"]["attention"]["score"], 5.0)
        self.assertEqual(result["domain_scores"]["delayed_recall"]["score"], 3.0)
        self.assertEqual(result["domain_scores"]["language"]["score"], 4.0)
        self.assertEqual(result["domain_scores"]["comprehension"]["score"], 3.0)
        self.assertEqual(result["domain_scores"]["visuospatial"]["score"], 2.0)

    def test_spelling_mode_attention_scoring(self):
        """
        Verify spelling 'WORLD' backwards option generates 5.0 points.
        """
        responses = {
            "attention_mode": "spelling",
            "attention_spelling": ["D", "L", "R", "O", "W"],
            "registration_words": [],
            "recall_words": []
        }
        result = calculate_assessment_score(responses)
        self.assertEqual(result["domain_scores"]["attention"]["score"], 5.0)

    def test_zero_score_empty_responses(self):
        """
        Verify empty or incorrect responses yield 0.0 points.
        """
        empty_responses = {
            "time_year": "1800",
            "time_season": "InvalidSeason",
            "time_month": "InvalidMonth",
            "time_date": "99",
            "time_day": "InvalidDay",
            "place_country": "",
            "place_state": "",
            "place_city": "",
            "place_setting": "None",
            "place_room": "",
            "registration_words": [],
            "attention_mode": "serial7",
            "attention_serial7": ["0", "0", "0", "0", "0"],
            "recall_words": [],
            "lang_naming_1": "",
            "lang_naming_2": "",
            "lang_repetition": "",
            "lang_fluency": "",
            "comp_step_1": False,
            "comp_step_2": False,
            "comp_step_3": False,
            "visuo_pentagon": "",
            "visuo_clock": ""
        }

        result = calculate_assessment_score(empty_responses)
        self.assertEqual(result["total_score"], 0.0)
        self.assertEqual(result["percentage_score"], 0.0)

    def test_step_validation(self):
        """
        Verify validation rules catch incomplete steps.
        """
        # Step 0 (Time) with missing fields
        is_valid, errors = validate_step(0, {"time_year": "2026"})
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # Step 2 (Registration) with missing words
        is_valid, errors = validate_step(2, {"registration_words": []})
        self.assertFalse(is_valid)

        # Step 2 (Registration) with words provided
        is_valid, errors = validate_step(2, {"registration_words": ["apple", "table"]})
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
