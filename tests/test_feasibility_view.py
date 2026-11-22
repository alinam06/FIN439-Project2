"""Presentation checks using existing default return levels."""

import unittest

from app import risk_chart
from src.feasibility_view import return_ceiling_chart
from src.portfolio import Mandate, analyze


class FeasibilityViewTests(unittest.TestCase):
    def test_ceiling_chart_reserves_readable_bands_and_labels_required_line(self):
        spec = return_ceiling_chart([("Reference", .0665), ("ETF downside", .058125)], .07).to_dict()
        self.assertGreaterEqual(spec["height"], 68)
        self.assertEqual(spec["layer"][0]["mark"]["size"], 20)
        self.assertEqual(spec["layer"][1]["mark"]["type"], "rule")
        self.assertIn("Required net return 7.00%", spec["title"]["subtitle"])

    def test_builder_labels_the_horizontal_target(self):
        mandate = Mandate()
        result = analyze(mandate)
        spec = risk_chart(result, mandate.target).to_dict()
        self.assertEqual(spec["layer"][0]["encoding"]["y"]["field"], "Net return")
        labels = [row["Label"] for rows in spec["datasets"].values() for row in rows if "Label" in row]
        self.assertEqual(labels, ["Required net return 7.00%"])
