import unittest

from who_messed_up.services.view_models.helpers import format_offset_seconds


class FormatOffsetSecondsTests(unittest.TestCase):
    def test_formats_pull_timestamp_as_minutes_and_decimal_seconds(self):
        self.assertEqual(format_offset_seconds(322_740), "5:22.74")
        self.assertEqual(format_offset_seconds(65_430), "1:05.43")
        self.assertEqual(format_offset_seconds(12_340), "0:12.34")

    def test_carries_rounded_seconds_into_the_next_minute(self):
        self.assertEqual(format_offset_seconds(59_999), "1:00.00")

    def test_preserves_unknown_timestamp_fallback(self):
        self.assertEqual(format_offset_seconds(None), "?")
        self.assertEqual(format_offset_seconds("invalid"), "?")


if __name__ == "__main__":
    unittest.main()
