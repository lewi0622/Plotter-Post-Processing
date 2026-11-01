"""Tests for pen-offset command generation and diameter validation."""

import unittest

from pen_offset import build_vpype_command, parse_diameter


class PenOffsetTests(unittest.TestCase):
    """Verify pen-offset math and generated Vpype commands."""

    def test_diameter_translation_matches_issue_example(self):
        """A larger layer pen translates negatively by half the diameter delta."""
        command = build_vpype_command(
            "input.svg",
            "output.svg",
            "-a stroke",
            0.35,
            {1: 0.5342},
            False,
            8.5,
            11,
        )

        self.assertIn("translate -l 1 -- -0.092in -0.092in", command)

    def test_crop_uses_page_dimensions(self):
        """The optional crop is appended with the selected page dimensions."""
        command = build_vpype_command(
            "input.svg",
            "output.svg",
            "-a stroke",
            0.35,
            {1: 0.35},
            True,
            8.5,
            11,
        )

        self.assertIn("crop 0in 0in 8.5in 11in", command)
        self.assertTrue(command.endswith('write "output.svg"'))
        self.assertNotIn("translate", command)

    def test_diameter_must_be_positive_and_finite(self):
        """Zero, negative, and non-finite diameters are rejected."""
        for value in ("0", "-0.1", "nan", "inf", "not a number"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_diameter(value, "Pen diameter")


if __name__ == "__main__":
    unittest.main()
