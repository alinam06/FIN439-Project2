from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

from src.historical import load_historical
from src.portfolio import Mandate
from src.stress import (
    PRESETS, StressInputs, assess_stress, decision, experiment_record,
    held_decision, historical_windows, preset,
)
from src.stress_report import render, replay
from test_historical import encode, fixture


class StressTests(unittest.TestCase):
    def setUp(self):
        self.base = Mandate()

    def test_recurring_cost_and_separate_transition_expense(self):
        inputs, mandate = preset("Higher investment costs", self.base)
        result = assess_stress(self.base, mandate, inputs)
        self.assertAlmostEqual(result.held.net_return, .069)
        self.assertAlmostEqual(result.stressed.max_net_return, .0701)
        self.assertAlmostEqual(result.candidate.net_return, .07)
        self.assertGreater(result.trade_drag, 0)
        gross_traded = sum(abs(a - b) for a, b in zip(result.held.weights, result.candidate.weights))
        self.assertAlmostEqual(result.trade_drag, gross_traded * .0025)
        without_trading_cost = assess_stress(self.base, mandate, replace(inputs, trade_cost=0))
        self.assertEqual(result.candidate.weights, without_trading_cost.candidate.weights)

    def test_equity_stress_defers_and_returns_no_candidate(self):
        inputs, mandate = preset("Equity market deterioration", self.base)
        result = assess_stress(self.base, mandate, inputs)
        self.assertAlmostEqual(result.stressed.max_net_return, .0561)
        self.assertIsNone(result.candidate)
        self.assertIsNone(result.trade_drag)
        self.assertEqual(result.held.weights, result.base.portfolios[-1].weights)
        self.assertEqual(decision(result.base)[0], "Due diligence")
        self.assertEqual(decision(result.stressed)[0], "Defer")
        self.assertIn("misses the target", held_decision(result.held))

    def test_invalid_covariance_and_cost_are_rejected(self):
        for inputs in (StressInputs(equity_bond_corr=1.3), StressInputs(equity_bond_corr=.50),
                       StressInputs(bond_vol_scale=0), StressInputs(annual_cost=-.001)):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                assess_stress(self.base, self.base, inputs)

    def test_reserve_bond_and_issuer_limits_are_enforced(self):
        mandate = replace(self.base, min_reserve=.15, min_bonds=.35, max_company=.02, target=.065)
        result = assess_stress(self.base, mandate, StressInputs())
        self.assertIn("Reject original weights", held_decision(result.held))
        bills, note, fund, _, company = result.candidate.weights
        self.assertGreaterEqual(bills + note + 1e-9, .15)
        self.assertGreaterEqual(note + fund + 1e-9, .35)
        self.assertLessEqual(company, .02 + 1e-9)
        self.assertGreaterEqual(result.candidate.net_return + 1e-9, mandate.target)
        self.assertAlmostEqual(sum(result.candidate.weights), 1)
        self.assertGreaterEqual(min(result.candidate.weights), -1e-9)
        self.assertEqual(result.candidate.verdict, "Unverified")

    def test_every_feasible_preset_leaves_due_diligence_open(self):
        for name in PRESETS:
            with self.subTest(name=name):
                inputs, mandate = preset(name, self.base)
                result = assess_stress(self.base, mandate, inputs)
                if result.candidate:
                    self.assertEqual(decision(result.stressed)[0], "Due diligence")
                    checks = {rule.name: rule.status for rule in result.candidate.rules}
                    self.assertNotIn("Fail", checks.values())
                    self.assertEqual(checks["Annual loss tolerance"], "Unverified")
                    self.assertEqual(checks["Issuer evidence"], "Unverified")

    def test_historical_missing_short_and_reviewed_windows(self):
        status, windows = historical_windows()
        self.assertIn("Unavailable", status)
        self.assertFalse(windows)
        source, meta = fixture()
        sample = load_historical(encode(source), meta)
        self.assertFalse(historical_windows(sample)[1])
        self.assertFalse(historical_windows(replace(sample, returns=sample.returns.tail(59)), reviewed=True)[1])
        _, windows = historical_windows(sample, reviewed=True)
        self.assertEqual(set(windows), {36, 60})
        self.assertEqual(windows[36][1], windows[60][1])
        self.assertNotEqual(windows[36][0], windows[60][0])
        np.testing.assert_allclose(windows[60][3], sample.covariance)

    def test_export_replays_and_saved_report_reproduces(self):
        inputs, mandate = preset("Higher investment costs", self.base)
        record = experiment_record("Test replay", self.base, mandate, inputs,
                                   assess_stress(self.base, mandate, inputs))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(replay(path), record)
        saved = Path(__file__).resolve().parents[1] / "outputs/stress-test-results.md"
        self.assertEqual(saved.read_text(encoding="utf-8"), render(date(2026, 11, 21)))


class StressViewTests(CleanCheckout):
    def test_infeasible_and_invalid_ui_cases(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        app.sidebar.selectbox[0].set_value("Risk & Scenario Analysis").run()
        app.selectbox(key="stress_preset").set_value("Combined adverse scenario").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("**REJECT** after reoptimization" in element.value for element in app.markdown))
        self.assertEqual(app.dataframe[1].value["Annual net return"].iloc[2], "Unavailable")
        app.selectbox(key="stress_preset").set_value("Custom stress").run()
        next(widget for widget in app.number_input
             if widget.label == "Global equity / IG fund correlation").set_value(.50).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Stop." in element.value for element in app.error))
        self.assertFalse(app.get("download_button"))
