"""Security research errors and calculations using synthetic provider fixtures."""

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import pandas as pd
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.data_workspace import DataWorkspace
from src.portfolio import Mandate
from src.security_research import (
    History, PROFILES, ResearchUnavailable, aligned_history, fetch_online,
    historical_metrics, mandate_notes, parse_history, provider_call, provider_profile, ticker_input,
)
from test_etf_portfolio import reviewed_fixture

APP = Path(__file__).resolve().parents[1] / "app.py"


def payload():
    values = {
        str(day.date()): {"4. close": "100.00", "5. adjusted close": str(100 * 1.01 ** i)}
        for i, day in enumerate(pd.date_range("2023-01-31", periods=14, freq="BME"))
    }
    return {"Meta Data": {"2. Symbol": "AAPL"}, "Monthly Adjusted Time Series": values}


class ResearchTests(CleanCheckout):
    def test_ticker_validation(self):
        self.assertEqual(ticker_input("  brk.b "), "BRK.B")
        for raw in ("", " aapl&apikey=x", "https://example.org", "V T", "A" * 13):
            with self.subTest(ticker=raw), self.assertRaises(ResearchUnavailable):
                ticker_input(raw)

    def test_missing_key_never_calls_provider(self):
        with patch("src.security_research.build_opener") as opener:
            with self.assertRaisesRegex(ResearchUnavailable, "ALPHAVANTAGE_API_KEY"):
                fetch_online("AAPL", "")
        opener.assert_not_called()

    def test_provider_errors_have_no_secret_or_raw_response(self):
        for response in ({"Note": "fixture-secret"}, {"Information": "fixture-secret"},
                         {"Error Message": "fixture-secret"}, ["fixture-secret"]):
            with self.subTest(response=response), patch("src.security_research.build_opener") as opener:
                opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
                with self.assertRaises(ResearchUnavailable) as failure:
                    provider_call("TIME_SERIES_MONTHLY_ADJUSTED", {"symbol": "AAPL"}, "fixture-secret")
                self.assertNotIn("fixture-secret", str(failure.exception))
        with patch("src.security_research.build_opener") as opener:
            opener.return_value.open.side_effect = URLError("fixture-secret")
            with self.assertRaisesRegex(ResearchUnavailable, "could not be reached"):
                provider_call("SYMBOL_SEARCH", {"keywords": "ABC"}, "fixture-secret")

    def test_adjusted_analytics_and_unadjusted_close_remain_separate(self):
        history = parse_history(payload(), "AAPL", datetime(2024, 2, 18))
        self.assertEqual(len(history.adjusted), 13)
        self.assertEqual(history.close.iloc[-1], 100)
        growth, drawdown, metrics, _ = historical_metrics(aligned_history({"AAPL": history}, 12))
        self.assertAlmostEqual(growth.iloc[-1, 0], 100 * 1.01 ** 12)
        self.assertAlmostEqual(metrics.iloc[0]["Annualized total return"], 1.01 ** 12 - 1)
        self.assertAlmostEqual(metrics.iloc[0]["Annualized volatility"], 0)
        self.assertAlmostEqual(drawdown.iloc[-1, 0], 0)
        prices = pd.DataFrame({"Synthetic": [100., 120., 90., 100.]})
        self.assertAlmostEqual(historical_metrics(prices)[2].iloc[0]["Maximum drawdown"], .25)

    def test_missing_month_missing_price_and_comparison_gap(self):
        source = payload()
        series = source["Monthly Adjusted Time Series"]
        series.pop("2023-08-31")
        with self.assertRaisesRegex(ResearchUnavailable, "gap"):
            parse_history(source, "AAPL", datetime(2024, 2, 18))
        source = payload()
        source["Monthly Adjusted Time Series"]["2023-08-31"].pop("5. adjusted close")
        with self.assertRaisesRegex(ResearchUnavailable, "missing or invalid"):
            parse_history(source, "AAPL", datetime(2024, 2, 18))
        good = parse_history(payload(), "AAPL", datetime(2024, 2, 18))
        bad = History(good.adjusted.iloc[1:], None, good.source, good.captured_at)
        with self.assertRaisesRegex(ResearchUnavailable, "13 matched"):
            aligned_history({"AAPL": good, "OTHER": bad}, 12)

    def test_exact_provider_classification_and_mandate_scope(self):
        data = {"bestMatches": [{"1. symbol": "ABC", "2. name": "Synthetic ETF", "3. type": "ETF",
                                 "4. region": "United States", "8. currency": "USD"}]}
        self.assertEqual(provider_profile(data, "ABC").kind, "ETF")
        with self.assertRaisesRegex(ResearchUnavailable, "No exact"):
            provider_profile(data, "AB")
        self.assertIn("default single-company cap is 8%", mandate_notes(PROFILES["NVDA"], Mandate(max_company=.04)))
        self.assertIn("4.00%", mandate_notes(PROFILES["NVDA"], Mandate(max_company=.04)))
        self.assertIn("10.00% active reserve floor", mandate_notes(PROFILES["BIL"], Mandate()))

    def test_offline_stock_profile_and_watchlist_preserve_portfolio(self):
        with patch.dict("os.environ", {"ALPHAVANTAGE_API_KEY": ""}), patch(
            "socket.getaddrinfo", side_effect=AssertionError("Network call in offline research")
        ):
            app = AppTest.from_file(str(APP)).run()
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            app.selectbox(key="research_topic").set_value("Security Search").run()
            app.selectbox(key="research_provider").set_value("Offline only").run()
            next(widget for widget in app.text_input if widget.label == "Ticker").set_value("AAPL")
            next(button for button in app.button if button.label == "Search securities").click().run()
            self.assertTrue(any("Apple Inc." in item.value for item in app.subheader))
            self.assertTrue(any("Latest price, date and historical risk metrics unavailable" in item.value
                                for item in app.caption))
            next(button for button in app.button if button.label == "Add AAPL to watchlist").click().run()
            self.assertTrue(any(widget.label == "Watchlist symbol" for widget in app.selectbox))
            app.selectbox(key="page").set_value("Investment Overview").run()
            self.assertEqual(app.metric[1].value, "7.11%")
            self.assertFalse(app.exception)

    def test_local_etfs_compare_offline_in_research_page(self):
        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                          "reviewed_panel_sha256": sample.csv_hash})
        workspace = DataWorkspace(sample, None, "Synthetic panel", "No archive")
        with patch("src.workspace_view.load_workspace", return_value=workspace):
            app = AppTest.from_file(str(APP)).run()
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            app.selectbox(key="research_topic").set_value("Security Search").run()
            next(widget for widget in app.text_input if widget.label == "Compare with (optional)").set_value("BIL")
            next(button for button in app.button if button.label == "Search securities").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get("vega_lite_chart")), 5)
            self.assertTrue(any("Monthly return correlation" in item.value for item in app.markdown))
            self.assertTrue(any("Latest adjusted observation" in item.value for item in app.markdown))
