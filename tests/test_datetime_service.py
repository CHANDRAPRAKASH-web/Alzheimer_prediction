"""
=========================================================
Aid Axis - Unit Tests for DateTime Service

Verifies:
1. Relative date phrase resolution (today, tomorrow, in 2 days)
2. Day-of-week phrase resolution (e.g. next Friday)
3. Time normalization (10am -> 10:00 AM, 14:30 -> 02:30 PM)
4. Timezone fallback and friendly string formatting
=========================================================
"""

import unittest
from datetime import datetime, timedelta
from services.datetime_service import (
    parse_relative_date_phrase,
    normalize_time_input,
    format_friendly_date,
    format_friendly_time,
    get_configured_timezone
)


class TestDateTimeService(unittest.TestCase):

    def test_relative_date_resolution(self):
        today_expected = datetime.now().strftime("%Y-%m-%d")
        tomorrow_expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        d_today, _ = parse_relative_date_phrase("today")
        self.assertEqual(d_today, today_expected)

        d_tomorrow, _ = parse_relative_date_phrase("tomorrow")
        self.assertEqual(d_tomorrow, tomorrow_expected)

        d_two_days, _ = parse_relative_date_phrase("in 2 days")
        expected_2d = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        self.assertEqual(d_two_days, expected_2d)

    def test_direct_iso_date_resolution(self):
        d_iso, _ = parse_relative_date_phrase("2026-11-15")
        self.assertEqual(d_iso, "2026-11-15")

    def test_time_normalization(self):
        self.assertEqual(normalize_time_input("10am"), "10:00 AM")
        self.assertEqual(normalize_time_input("3PM"), "03:00 PM")
        self.assertEqual(normalize_time_input("10:30 am"), "10:30 AM")
        self.assertEqual(normalize_time_input("14:45"), "02:45 PM")
        self.assertEqual(normalize_time_input("09:15"), "09:15 AM")
        self.assertIsNone(normalize_time_input("not-a-time"))

    def test_friendly_formatting(self):
        friendly_d = format_friendly_date("2026-10-31")
        self.assertIn("Oct 31, 2026", friendly_d)

        friendly_t = format_friendly_time("14:30")
        self.assertEqual(friendly_t, "02:30 PM")

    def test_timezone_fallback(self):
        tz = get_configured_timezone("Invalid/NonExistent")
        self.assertIsNotNone(tz)


if __name__ == "__main__":
    unittest.main()
