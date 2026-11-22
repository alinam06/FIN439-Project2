"""Synthetic HTTP and interface checks for the keyless Market History path."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pandas as pd
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.keyless_market import NY, fetch_market_history, parse_bars, read_api
from src.security_research import History, ResearchUnavailable, aligned_history

APP = Path(__file__).resolve().parents[1] / "app.py"


def bars(ticker):
    dates = pd.date_range("2024-01-31", periods=14, freq="BME", tz=NY)
    return "\n".join(json.dumps({"timestamp": point.tz_convert("UTC").isoformat(), "symbol": ticker,
                                  "symbol_id": 9, "close": 100 + i}) for i, point in enumerate(dates)).encode()


class KeylessMarketTests(CleanCheckout):
    def test_raw_prices_use_new_york_months_and_exclude_open_day(self):
        history = parse_bars(bars("SPY"), "SPY", datetime(2025, 2, 28, 12, tzinfo=NY))
        self.assertEqual(history.basis, "price")
        self.assertEqual(str(history.daily_close.index[-1].date()), "2025-01-31")
        self.assertEqual(history.close.iloc[-1], 112)
        adjusted = History(history.adjusted, None, "Synthetic adjusted fixture", "")
        with self.assertRaisesRegex(ResearchUnavailable, "cannot be compared"):
            aligned_history({"SPY": history, "Other": adjusted}, 12)

    def test_reused_ticker_and_provider_errors(self):
        with self.assertRaisesRegex(ResearchUnavailable, "mismatched"):
            parse_bars(bars("SPY"), "VT", datetime(2025, 2, 28, 12, tzinfo=NY))
        for error, message in ((HTTPError("example", 429, "limit", None, None), "rate limit"),
                               (HTTPError("example", 404, "unknown", None, None), "No Market History data"),
                               (URLError("offline"), "could not be reached")):
            with self.subTest(message=message), patch("src.keyless_market.build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaisesRegex(ResearchUnavailable, message):
                    read_api("/bars/stocks/us/SPY/1d")

    def test_unknown_keyless_ticker_can_use_catalogue_metadata(self):
        with patch("src.keyless_market.read_api", side_effect=[
            bars("ABCD"), b'{"contract": {"name": "Synthetic Listing Inc."}}'
        ]) as read:
            profile, history = fetch_market_history("abcd")
        self.assertEqual(profile.name, "Synthetic Listing Inc.")
        self.assertEqual(history.basis, "price")
        self.assertTrue(read.call_args_list[0].args[0].startswith("/bars/stocks/us/ABCD/1d?"))
        self.assertNotIn("apikey", read.call_args_list[0].args[0])

    def test_browser_session_defaults_keyless_and_uses_success_cache(self):
        from dataclasses import replace
        from src.security_research import PROFILES

        old = parse_bars(bars("SPY"), "SPY", datetime(2025, 3, 15, tzinfo=NY))
        history = replace(old, captured_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
        with (patch.dict("os.environ", {"ALPHAVANTAGE_API_KEY": "", "ALPHA_VANTAGE_API_KEY": ""}),
              patch("src.security_view.fetch_market_history", return_value=(PROFILES["SPY"], history)) as fetch,
              patch("src.security_view.fetch_online") as alpha):
            app = AppTest.from_file(str(APP)).run()
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            app.selectbox(key="research_topic").set_value("Security Search").run()
            self.assertEqual(app.selectbox(key="research_provider").value, "Market History (no key)")
            next(item for item in app.text_input if item.label == "Ticker").set_value("SPY")
            next(item for item in app.button if item.label == "Search securities").click().run()
            self.assertIn("Annualized price change", app.dataframe[0].value.columns)
            self.assertTrue(any("Price-only series" in item.value for item in app.caption))
            self.assertFalse(app.exception)
            next(item for item in app.button if item.label == "Search securities").click().run()
            fetch.assert_called_once_with("SPY")
            alpha.assert_not_called()
