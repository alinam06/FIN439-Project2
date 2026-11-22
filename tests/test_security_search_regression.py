"""Regressions for the submitted security search flow (synthetic provider responses)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.security_research import PROFILES, parse_history
from test_security_research import payload

APP = Path(__file__).resolve().parents[1] / "app.py"


class SearchRegressionTests(CleanCheckout):
    def test_alias_key_enables_search_on_first_submit(self):
        with patch.dict("os.environ", {"ALPHAVANTAGE_API_KEY": "", "ALPHA_VANTAGE_API_KEY": "fixture-key"}):
            with patch("src.security_view.fetch_online") as fetch:
                fetch.return_value = PROFILES["AAPL"], parse_history(payload(), "AAPL", datetime(2024, 2, 18))
                app = AppTest.from_file(str(APP)).run()
                app.selectbox(key="page").set_value("Portfolio Builder").run()
                app.selectbox(key="builder_view").set_value("Research and data").run()
                app.selectbox(key="research_topic").set_value("Security Search").run()
                # Simulate a session that previously saved the former checkbox as off.
                app.session_state["research_online_True"] = False
                app.selectbox(key="research_provider").set_value("Alpha Vantage").run()
                next(item for item in app.text_input if item.label == "Ticker").set_value("AAPL")
                next(item for item in app.button if item.label == "Search securities").click().run()
                fetch.assert_called_once_with("AAPL", "fixture-key")
                self.assertTrue(any("Latest completed monthly close" in item.value for item in app.markdown))
                self.assertEqual([item.message for item in app.exception], [])

    def test_clean_checkout_demo_has_charts_without_fetching(self):
        with patch.dict("os.environ", {"ALPHAVANTAGE_API_KEY": "", "ALPHA_VANTAGE_API_KEY": ""}):
            with patch("src.security_view.fetch_online") as fetch:
                app = AppTest.from_file(str(APP)).run()
                app.selectbox(key="page").set_value("Portfolio Builder").run()
                app.selectbox(key="builder_view").set_value("Research and data").run()
                app.selectbox(key="research_topic").set_value("Security Search").run()
                next(item for item in app.button if item.label == "Try the offline demonstration").click().run()
                self.assertTrue(any("hypothetical series are invented" in item.value for item in app.info))
                self.assertEqual(len(app.get("vega_lite_chart")), 5)
                self.assertEqual([item.message for item in app.exception], [])
                fetch.assert_not_called()

    def test_stale_provider_history_retries_and_reports_cached_fallback(self):
        from src.security_research import ResearchUnavailable

        old_history = parse_history(payload(), "AAPL", datetime(2024, 2, 18))
        with patch.dict("os.environ", {"ALPHAVANTAGE_API_KEY": "fixture-key", "ALPHA_VANTAGE_API_KEY": "alternate"}):
            with patch("src.security_view.fetch_online", side_effect=[
                (PROFILES["AAPL"], old_history), ResearchUnavailable("Alpha Vantage rate limit reached.")
            ]) as fetch:
                app = AppTest.from_file(str(APP)).run()
                app.selectbox(key="page").set_value("Portfolio Builder").run()
                app.selectbox(key="builder_view").set_value("Research and data").run()
                app.selectbox(key="research_topic").set_value("Security Search").run()
                app.selectbox(key="research_provider").set_value("Alpha Vantage").run()
                next(item for item in app.text_input if item.label == "Ticker").set_value("AAPL")
                next(item for item in app.button if item.label == "Search securities").click().run()
                next(item for item in app.button if item.label == "Search securities").click().run()
                self.assertEqual(fetch.call_count, 2)
                self.assertEqual(fetch.call_args.args, ("AAPL", "fixture-key"))
                self.assertTrue(any("rate limit" in item.value and "last successful" in item.value
                                    for item in app.warning))
                self.assertEqual(len(app.get("vega_lite_chart")), 4)
                self.assertFalse(app.exception)

    def test_adjusted_history_survives_missing_unadjusted_close(self):
        source = payload()
        source["Monthly Adjusted Time Series"]["2023-08-31"].pop("4. close")
        history = parse_history(source, "AAPL", datetime(2024, 2, 18))
        self.assertIsNone(history.close)
        self.assertEqual(len(history.adjusted), 13)
