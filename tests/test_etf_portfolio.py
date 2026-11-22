"""Synthetic data tests for the ETF and authorized-import paths."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

import numpy as np

from clean_checkout import CleanCheckout

from src.etf_portfolio import analyze_windows, snapshot_date
from src.historical import TICKERS, load_historical
from src.market_import import align
from src.portfolio import Mandate
from test_historical import encode, fixture


def reviewed_fixture():
    prices, metadata = fixture()
    rng = np.random.default_rng(432)
    changes = rng.normal(0, [.002, .017, .022, .045], size=(60, len(TICKERS)))
    changes[-36:, 3] *= 1.4
    prices.iloc[:, :] = 100 * np.vstack([np.ones(4), np.cumprod(1 + changes, axis=0)])
    return load_historical(encode(prices), metadata)


class ETFPortfolioTests(CleanCheckout):
    def test_windows_share_assumptions_and_have_distinct_risk(self):
        sample = reviewed_fixture()
        first, second = analyze_windows(sample, Mandate(), snapshot_date(sample),
                                        [.035, .045, .055, .10], .0015, reviewed=True)
        self.assertEqual((first.months, second.months), (36, 60))
        self.assertLess(first.first_price_date, second.last_price_date)
        self.assertNotEqual(first.first_price_date, second.first_price_date)
        self.assertEqual(first.last_price_date, second.last_price_date)
        self.assertAlmostEqual(first.max_net_return, second.max_net_return)
        self.assertEqual(first.portfolios["60% VT / 40% LQD"].weights, (0, 0, .4, .6))
        self.assertNotEqual(first.portfolios["60% VT / 40% LQD"].volatility,
                            second.portfolios["60% VT / 40% LQD"].volatility)
        for window in (first, second):
            case = window.portfolios["Constrained candidate"]
            self.assertEqual(case.verdict, "Unverified")
            self.assertAlmostEqual(sum(case.weights), 1)
            self.assertGreaterEqual(case.weights[0] + 1e-9, .10)
            self.assertGreaterEqual(sum(case.weights[1:3]) + 1e-9, .25)
            self.assertGreaterEqual(case.net_return + 1e-9, .07)

    def test_target_is_infeasible_with_lower_forward_returns(self):
        sample = reviewed_fixture()
        for window in analyze_windows(sample, Mandate(), snapshot_date(sample),
                                      [.02, .03, .04, .05], .0015, reviewed=True):
            self.assertNotIn("Constrained candidate", window.portfolios)
            self.assertIn("Defer", window.decision)

    def test_missing_review_wrong_cutoff_and_singular_risk_stop(self):
        sample = reviewed_fixture()
        with self.assertRaisesRegex(ValueError, "Review provider"):
            analyze_windows(sample, Mandate(), snapshot_date(sample), [.03] * 4, 0)
        with self.assertRaisesRegex(ValueError, "capture date"):
            analyze_windows(sample, Mandate(), date(2024, 1, 1), [.03] * 4, 0, reviewed=True)
        prices, metadata = fixture()
        singular = load_historical(encode(prices), metadata)
        with self.assertRaisesRegex(ValueError, "singular or ill-conditioned"):
            analyze_windows(singular, Mandate(), snapshot_date(singular), [.03] * 4, 0, reviewed=True)

    def test_aligner_uses_adjusted_close_and_requires_matching_dates(self):
        sample = reviewed_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for ticker in TICKERS:
                lines = ["timestamp,close,adjusted_close"]
                lines.extend(f"{day.date()},9999,{value}" for day, value in sample.prices[ticker].items())
                (directory / f"{ticker}.csv").write_text("\n".join(lines), encoding="utf-8")
            output = align(directory, "2024-01")
            self.assertEqual(len(output), 62)
            self.assertNotIn("9999", output[1])
            file = directory / "VT.csv"
            file.write_text(file.read_text().replace("2024-01-31", "2024-01-30"))
            with self.assertRaisesRegex(ValueError, "session dates differ"):
                align(directory, "2024-01")

    def test_upload_view_records_forward_assumptions_and_runs_both_windows(self):
        import io
        import json
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest

        sample = reviewed_fixture()
        uploads = {"Aligned adjusted prices": encode(sample.prices),
                   "Source metadata": json.dumps(sample.metadata).encode()}
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Research and data").run()
        app.selectbox(key="research_topic").set_value("Historical Market Data")
        app.selectbox(key="data_import").set_value("ETF panel")
        with patch("streamlit.file_uploader", side_effect=lambda label, **_: io.BytesIO(uploads[label])):
            app.run()
            next(widget for widget in app.checkbox if "reconciled" in widget.label).check()
            app.text_area[0].set_value("Synthetic regression assumptions, not market estimates.")
            returns = (3.5, 4.5, 5.5, 10.0)
            rate_inputs = [field for field in app.number_input if "forward return" in field.label]
            for field, value in zip(rate_inputs, returns):
                field.set_value(value)
            app.run()
        self.assertFalse(app.exception)
        self.assertTrue(app.get("download_button"))
        self.assertEqual(set(app.dataframe[-1].value["Months"].astype(int)), {36, 60})
