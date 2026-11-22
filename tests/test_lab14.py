"""Independent course fixtures, without the Version 1 fee or fifth asset."""

import unittest

import numpy as np

from src.portfolio import covariance, portfolio_metrics


RETURNS = [.035, .043, .050, .080]
VOLATILITIES = [.005, .070, .060, .160]
CORRELATIONS = np.array([
    [1, .10, .05, .00],
    [.10, 1, .80, -.10],
    [.05, .80, 1, .25],
    [.00, -.10, .25, 1],
])
BENCHMARK = [0, 0, .40, .60]
DISPLAY_TOLERANCE = .00005  # Half of 0.01 percentage point, expressed as a decimal.


class Lab14Tests(unittest.TestCase):
    def test_three_course_portfolios(self):
        reciprocal = 1 / np.array(VOLATILITIES)
        portfolios = (
            ("benchmark", BENCHMARK, .0680, .1046),
            ("equal weight", [.25] * 4, .0520, .0521),
            ("inverse volatility", reciprocal / reciprocal.sum(), .0377, .0105),
        )
        risk = covariance(VOLATILITIES, CORRELATIONS)
        for name, weights, expected_return, expected_volatility in portfolios:
            with self.subTest(portfolio=name):
                gross, net, volatility = portfolio_metrics(weights, RETURNS, risk)
                self.assertAlmostEqual(gross, expected_return, delta=DISPLAY_TOLERANCE)
                self.assertEqual(net, gross)
                self.assertAlmostEqual(volatility, expected_volatility, delta=DISPLAY_TOLERANCE)

    def test_changed_correlation_raises_benchmark_volatility(self):
        changed = CORRELATIONS.copy()
        changed[2, 3] = changed[3, 2] = .50
        original = portfolio_metrics(BENCHMARK, RETURNS, covariance(VOLATILITIES, CORRELATIONS))
        revised = portfolio_metrics(BENCHMARK, RETURNS, covariance(VOLATILITIES, changed))
        self.assertEqual(revised[:2], original[:2])
        self.assertGreater(revised[2], original[2])
        self.assertAlmostEqual(revised[2], .1100, delta=DISPLAY_TOLERANCE)

    def test_impossible_and_asymmetric_correlations_rejected(self):
        invalid = CORRELATIONS.copy()
        invalid[0, 1] = invalid[1, 0] = 1.30
        with self.assertRaisesRegex(ValueError, "symmetric correlations"):
            covariance(VOLATILITIES, invalid)
        invalid = CORRELATIONS.copy()
        invalid[0, 1] = .20
        with self.assertRaisesRegex(ValueError, "symmetric correlations"):
            covariance(VOLATILITIES, invalid)

    def test_positive_semidefiniteness_and_singular_risk_measurement(self):
        risk = covariance(VOLATILITIES, CORRELATIONS)
        self.assertGreaterEqual(np.linalg.eigvalsh(risk)[0], -1e-12)
        indefinite = [[1, .9, .9], [.9, 1, -.9], [.9, -.9, 1]]
        with self.assertRaisesRegex(ValueError, "positive semidefinite"):
            covariance([.1] * 3, indefinite)
        singular = covariance([.1, .1], [[1, -1], [-1, 1]])
        self.assertAlmostEqual(portfolio_metrics([.5, .5], [.04, .06], singular)[2], 0)

    def test_invalid_weights_rejected(self):
        risk = covariance(VOLATILITIES, CORRELATIONS)
        for weights in ([.2] * 4, [.5] * 4, [-.1, .1, .4, .6], [0, 0, 1], [0, 0, .4, np.nan]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                portfolio_metrics(weights, RETURNS, risk)
