"""Independent checks of investment judgment calculations and active-state wiring."""

from dataclasses import replace
from math import sqrt
from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

from src.committee import recommendation
from src.economic_signal import Signal
from src.investment_context import build_context
from src.judgment import (
    attribution, committee_panel, reserve_sensitivity, resilience, restrictions,
    signal_admission, transition,
)
from src.portfolio import Mandate, analyze
from src.stress import assess_stress, preset

APP = Path(__file__).resolve().parents[1] / "app.py"


class JudgmentTests(CleanCheckout):
    def test_attribution_known_answer_signed_marginal_risk(self):
        weights = (.75, .25)
        # 10% and 20% vol, perfectly negatively correlated. The second sleeve hedges the first.
        risk = [[.01, -.02], [-.02, .04]]
        result = attribution(weights, (.08, .04), risk, .002)
        self.assertAlmostEqual(result.gross_return, .07)
        self.assertAlmostEqual(sum(result.gross_by_asset) - result.annual_cost, result.net_return)
        self.assertAlmostEqual(result.volatility, .025)
        self.assertAlmostEqual(result.risk_by_asset[0], .075)
        self.assertAlmostEqual(result.risk_by_asset[1], -.05)
        self.assertAlmostEqual(sum(result.risk_by_asset), result.volatility)
        zero = attribution((.5, .5), (.08, .04), [[.01, -.01], [-.01, .01]], 0)
        self.assertEqual(zero.volatility, 0)
        self.assertIsNone(zero.risk_by_asset)
        with self.assertRaises(ValueError):
            attribution(weights, (.08, .04), None, 0)

    def test_attribution_matches_engine_and_finite_difference(self):
        context = build_context(Mandate())
        active = context.active
        risk = context.risk
        weights = np.asarray(active.weights)
        result = attribution(weights, context.gross_returns, risk, context.annual_cost)
        self.assertAlmostEqual(sum(result.risk_by_asset), active.volatility)
        self.assertAlmostEqual(sum(result.gross_by_asset) - result.annual_cost, active.net_return)
        for index, weight in enumerate(weights):
            step = np.eye(len(weights))[index] * 1e-6
            above, below = weights + step, weights - step
            derivative = (sqrt(above @ risk @ above) - sqrt(below @ risk @ below)) / 2e-6
            self.assertAlmostEqual(derivative * weight, result.risk_by_asset[index], places=8)

    def test_turnover_reconciles_buys_sells_and_trade_expense(self):
        context = build_context(Mandate())
        inputs, challenged = preset("Higher investment costs", context.mandate)
        result = assess_stress(context.mandate, challenged, inputs)
        traded = transition(context.active, result.candidate, context.mandate.portfolio_value, inputs.trade_cost)
        buys = sum(max(0, new - old) for old, new in zip(context.active.weights, result.candidate.weights))
        self.assertAlmostEqual(traded.one_way_share, buys)
        self.assertAlmostEqual(traded.gross_share, result.traded_share)
        self.assertAlmostEqual(traded.expense, result.trade_drag * 5_000_000)
        self.assertEqual(traded.largest_index, 4)
        self.assertAlmostEqual(result.held.net_return, .069)
        self.assertAlmostEqual(result.stressed.max_net_return, .0701)
        inputs, challenged = preset("Equity market deterioration", context.mandate)
        result = assess_stress(context.mandate, challenged, inputs)
        self.assertIsNone(transition(context.active, result.candidate, 5_000_000, 0))
        self.assertIn("exceeds", result.stressed.decision)

    def test_reverse_thresholds_agree_with_optimizer_on_either_side(self):
        context = build_context(Mandate())
        bounds = resilience(context)
        self.assertAlmostEqual(bounds.held_cost_break_even, .0015)
        self.assertAlmostEqual(bounds.feasible_cost_break_even, .0026)
        self.assertAlmostEqual(bounds.held_equity_cut, 0)
        for direction in (-1, 1):
            cost_case = analyze(context.mandate, frontier_points=0, annual_cost=bounds.feasible_cost_break_even + direction * 1e-5)
            self.assertEqual(len(cost_case.portfolios), 3 if direction < 0 else 2)
            gross = list(context.gross_returns)
            gross[3] -= bounds.feasible_equity_cut + direction * 1e-5
            gross[4] -= bounds.feasible_equity_cut + direction * 1e-5
            equity_case = analyze(context.mandate, frontier_points=0, gross_returns=gross)
            self.assertEqual(len(equity_case.portfolios), 3 if direction < 0 else 2)
        floor, ceiling = reserve_sensitivity(context)
        self.assertAlmostEqual(ceiling, analyze(replace(context.mandate, min_reserve=floor), frontier_points=0).max_net_return)
        self.assertAlmostEqual(ceiling, .07103)
        for check in restrictions(context):
            if check.objective:
                self.assertEqual(check.status, "At limit")

    def test_panel_respects_veto_and_missing_signal(self):
        base = build_context(Mandate())
        failed = build_context(Mandate(), weights=(1, 0, 0, 0, 0))
        infeasible = build_context(replace(Mandate(), target=.10))
        for context, action in ((base, "ILLUSTRATIVE ONLY"), (failed, "REJECT"), (infeasible, "REJECT")):
            panel = committee_panel(context, None, "ADOPT")
            self.assertEqual(panel.action, recommendation(context.proposal, requested="ADOPT", illustrative=True).action)
            self.assertEqual(panel.action, action)
            self.assertIn("0%", panel.implementation)
        self.assertEqual(signal_admission(None)[0], "Quarantine")
        self.assertEqual(signal_admission(None, source_rejected=True)[0], "Reject")
        self.assertEqual(signal_admission(Signal("Review", "Eligible", change_pp=.12))[0], "Admit for monitoring")

    def test_interactive_judgment_uses_current_scenario(self):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
        app.selectbox(key="stress_preset").set_value("Higher investment costs").run()
        self.assertTrue(any("4.07% ($203,653)" in m.value for m in app.caption))
        app.selectbox(key="page").set_value("Investment Assistant").run()
        app.chat_input[0].set_value("Why did the optimizer change the weights? Show turnover.").run()
        self.assertTrue(any("4.07%" in m.value for m in app.markdown))
        app.radio(key="scenario_mode").set_value("Custom scenario").run()
        app.number_input(key="scenario_target").set_value(7.5).run()
        app.chat_input[0].set_value("What is the break-even cost?").run()
        self.assertTrue(any("-24.0 bp" in m.value for m in app.markdown))
        app.selectbox(key="page").set_value("Committee Decision").run()
        self.assertTrue(any("Reassess only when a candidate meets the net objective" in m.value for m in app.markdown))
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
