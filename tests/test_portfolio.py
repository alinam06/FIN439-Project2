from dataclasses import replace
from pathlib import Path
import unittest

import numpy as np

from src.assumptions import ASSETS, CORRELATIONS
from src.portfolio import Mandate, analyze, covariance
from src.report import render


class PortfolioTests(unittest.TestCase):
    def test_lab_14_benchmark_less_illustrative_fee(self):
        equal, benchmark, _ = analyze(Mandate(), frontier_points=0).portfolios
        self.assertEqual(benchmark.weights, (0, 0, .4, .6, 0))
        self.assertAlmostEqual(benchmark.net_return, .0665)
        self.assertAlmostEqual(benchmark.volatility, .1046135746)
        self.assertAlmostEqual(equal.net_return, .0581)

    def test_default_optimum_and_required_evidence(self):
        mandate = Mandate()
        result = analyze(mandate)
        self.assertAlmostEqual(result.max_net_return, .0711)
        optimized = result.portfolios[-1]
        self.assertAlmostEqual(optimized.net_return, mandate.target)
        self.assertAlmostEqual(optimized.volatility, .1210, places=4)
        self.assertAlmostEqual(sum(optimized.weights), 1)
        statuses = {rule.name: rule.status for rule in optimized.rules}
        for name in ("Issuer evidence", "Redeemable within five business days",
                     "Annual loss tolerance", "No derivatives", "Underlying fund leverage",
                     "Annual rebalancing"):
            self.assertEqual(statuses[name], "Unverified")
        self.assertNotIn("Fail", statuses.values())
        self.assertEqual(optimized.verdict, "Unverified")
        self.assertEqual([p.verdict for p in result.portfolios[:2]], ["Fail", "Fail"])
        self.assertIn("due diligence", result.decision)
        self.assertAlmostEqual(result.frontier[-1][1], result.max_net_return)
        for left, right in zip(result.frontier, result.frontier[1:]):
            self.assertLessEqual(left[0], right[0] + 1e-9)
            self.assertLessEqual(left[1], right[1] + 1e-9)

    def test_lab_13_default_inputs_and_compounding(self):
        mandate = Mandate()
        self.assertEqual((mandate.portfolio_value, mandate.horizon, mandate.target),
                         (5_000_000, 15, .07))
        self.assertEqual((mandate.min_bonds, mandate.min_reserve, mandate.max_company,
                          mandate.min_five_day), (.25, .10, .08, .90))
        self.assertAlmostEqual(mandate.target_value, 13_795_157.7035767, places=2)

    def test_default_optimum_matches_closed_form_on_binding_face(self):
        risk = covariance([asset.volatility for asset in ASSETS], CORRELATIONS)
        # Fix bills at zero, note at 10%, and impose 7.15% gross return and full investment.
        # Vary only the company's weight x. The directional derivative vanishes at the minimum.
        base = np.array([0, .10, .16, .74, 0])
        direction = np.array([0, 0, 1 / 3, -4 / 3, 1])
        minimum = base - (direction @ risk @ base) / (direction @ risk @ direction) * direction
        optimized = analyze(Mandate(), frontier_points=0).portfolios[-1]
        np.testing.assert_allclose(optimized.weights, minimum, atol=1e-9, rtol=0)

    def test_target_above_ceiling_keeps_benchmarks(self):
        result = analyze(replace(Mandate(), target=.075))
        self.assertEqual(len(result.portfolios), 2)
        self.assertLess(result.max_net_return, .075)
        self.assertTrue(result.frontier)
        self.assertIn("Defer", result.decision)

    def test_tightening_issuer_cap_changes_allocation_and_ceiling(self):
        result = analyze(replace(Mandate(), max_company=0), frontier_points=0)
        self.assertAlmostEqual(result.max_net_return, .0703)
        self.assertEqual(result.portfolios[-1].weights[-1], 0)

    def test_overlapping_rules_allow_all_treasury_note(self):
        mandate = Mandate(target=0, min_bonds=1, min_reserve=1)
        result = analyze(mandate)
        self.assertEqual(len(result.portfolios), 3)
        np.testing.assert_allclose(result.portfolios[-1].weights, [0, 1, 0, 0, 0], atol=1e-9)
        self.assertAlmostEqual(result.max_net_return, .0415)

    def test_target_exactly_at_ceiling(self):
        mandate = Mandate(target=.0711)
        result = analyze(mandate, frontier_points=0)
        np.testing.assert_allclose(result.portfolios[-1].weights, [0, .1, .15, .67, .08], atol=1e-9)

    def test_invalid_covariance_and_mandate(self):
        invalid = np.array(CORRELATIONS)
        invalid[0, 1] = invalid[1, 0] = 1.3
        with self.assertRaises(ValueError):
            covariance([asset.volatility for asset in ASSETS], invalid)
        for changes in ({"portfolio_value": 0}, {"target": float("nan")}, {"min_reserve": 1.01}, {"horizon": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Mandate(**changes)

    def test_saved_markdown_matches_generated_report(self):
        report = Path(__file__).resolve().parents[1] / "outputs" / "version_1_results.md"
        self.assertEqual(report.read_text(encoding="utf-8"), render())
