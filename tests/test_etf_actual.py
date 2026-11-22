"""Licensed snapshot checks run when the private source files are present."""

from datetime import date
from pathlib import Path
import unittest

import numpy as np
from streamlit.testing.v1 import AppTest

from src.assumptions import ANNUAL_COST
from src.data_workspace import load_workspace
from src.etf_decision_view import reviewed_panel
from src.etf_evidence import FORWARD, audit, render
from src.etf_portfolio import analyze_windows, snapshot_date
from src.portfolio import Mandate

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT / "data/etf-prices.csv").exists(), "Private reviewed ETF snapshot not installed")
class ActualETFTests(unittest.TestCase):
    def test_source_audit_and_dates(self):
        sample = load_workspace().etf
        source = audit(ROOT / "data/raw")
        self.assertTrue(reviewed_panel(sample))
        self.assertEqual(sample.sample_dates, (date(2021, 10, 29), date(2026, 10, 30)))
        self.assertEqual(sample.returns.shape, (60, 4))
        self.assertFalse(sample.warnings)
        self.assertEqual([item["raw_rows"] for item in source.values()], [234, 292, 292, 221])
        self.assertEqual([item["positive_distribution_months"] for item in source.values()], [50, 56, 56, 20])
        self.assertEqual(source, sample.metadata["raw_audit"])
        np.testing.assert_allclose(sample.returns.iloc[0], sample.prices.iloc[1] / sample.prices.iloc[0] - 1)
        self.assertGreater(sample.correlation.loc["IEF", "LQD"], .90)

    def test_actual_windows_and_reports(self):
        sample = load_workspace().etf
        windows = analyze_windows(sample, Mandate(), snapshot_date(sample), FORWARD, ANNUAL_COST, reviewed=True)
        for window in windows:
            self.assertAlmostEqual(window.max_net_return, .0665)
            self.assertNotIn("Constrained candidate", window.portfolios)
        self.assertLess(windows[0].portfolios["60% VT / 40% LQD"].volatility,
                        windows[1].portfolios["60% VT / 40% LQD"].volatility)
        for filename, text in zip(("etf-analysis-results.md", "historical-window-comparison.md"), render(sample)):
            self.assertEqual((ROOT / "outputs" / filename).read_text(encoding="utf-8"), text)

    def test_executive_uses_actual_data_and_classroom_remains_selectable(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, "6.65%")
        model = next(widget for widget in app.selectbox if widget.label == "Decision model")
        model.set_value("Reviewed ETF snapshot").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, "6.65%")
        self.assertTrue(any("REJECT" in item.value for item in app.warning))
        next(widget for widget in app.selectbox if widget.label == "Decision model").set_value(
            "Classroom demonstration").run()
        self.assertEqual(app.metric[1].value, "7.11%")
