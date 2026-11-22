"""Financial question coverage and contextual chat behavior."""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.analyst import SUGGESTIONS, UNSUPPORTED, answer_question
from src.data_workspace import DataWorkspace
from src.economic_signal import Signal
from src.investment_context import ETF, build_context
from src.portfolio import Mandate
from test_etf_portfolio import reviewed_fixture

APP = Path(__file__).resolve().parents[1] / "app.py"


class AnalystTests(CleanCheckout):
    def test_question_categories_and_phrasing(self):
        context = build_context(Mandate())
        cases = {
            "Can you explain why the committee recommends a pilot?": "ILLUSTRATIVE ONLY",
            "What are my largest investment risks?": "contributors to modeled variance",
            "How much money is allocated to each asset?": "Treasury bills",
            "Am I meeting my return objective?": "meets",
            "What's the highest achievable return?": "7.11%",
            "Which investment constraints am I violating?": "Failed checks: none",
            "How does correlation affect the portfolio?": "perfect positive correlation",
            "Why is diversification important?": "perfect positive correlation",
            "How does an efficient frontier work?": "lowest modeled annual volatility",
            "What happens under the selected stress scenario?": "Standard sensitivity",
            "How do expected and historical returns differ?": "realized sample performance",
            "Why do the classroom and ETF models differ?": "fictional company sleeve",
            "What would make the committee reconsider?": "loss tolerance",
            "What is the economic signal telling me?": "unavailable",
            "What is our annual expense?": "$7,500",
            "How long is the investor's horizon?": "15 years",
            "Show me optimization results": "12.10%",
        }
        for question, fragment in cases.items():
            with self.subTest(question=question):
                self.assertIn(fragment, answer_question(question, context, None, "PILOT"))
        for unsupported in ("Write a poem about portfolio risk", "Do you know tomorrow's weather?",
                            "Buy 20 shares for me", "Which stocks should I trade?"):
            self.assertEqual(answer_question(unsupported, context, None, "PILOT"), UNSUPPORTED)
        signal = Signal("Review", "Credit spread widened.", change_pp=.12)
        self.assertIn("+12 bp", answer_question("What's the credit signal?", context, signal, "PILOT"))
        self.assertIn("could not be evaluated", answer_question(
            "How did the stress go?", context, None, "PILOT", stress_failed=True))

    def test_history_suggestions_clear_and_updated_target(self):
        with patch("socket.getaddrinfo", side_effect=AssertionError("Analyst requested network access")):
            app = AppTest.from_file(str(APP)).run()
            app.selectbox(key="page").set_value("Investment Assistant").run()
            next(button for button in app.button if button.label == SUGGESTIONS[0]).click().run()
            self.assertTrue(any("**ILLUSTRATIVE ONLY**" in item.value for item in app.markdown))
            app.chat_input[0].set_value("Tell me tomorrow's weather").run()
            self.assertTrue(any(UNSUPPORTED == item.value for item in app.markdown))
            self.assertEqual(len(app.get("chat_message")), 4)
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            app.number_input(key="scenario_target").set_value(7.5).run()
            app.chat_input[0].set_value("Why is my portfolio being rejected?").run()
            self.assertTrue(any("**REJECT**" in item.value and "maximum" in item.value for item in app.markdown))
            self.assertTrue(any("Earlier scenario" in item.value for item in app.caption))
            next(button for button in app.button if button.label == "Clear conversation").click().run()
            self.assertEqual(len(app.get("chat_message")), 0)
            next(button for button in app.button if button.label == "Reset to default").click().run()
            app.chat_input[0].set_value("What is my return target?").run()
            self.assertTrue(any("**7.00%**" in item.value for item in app.markdown))
            self.assertFalse(app.exception)
            self.assertFalse(app.error)

    def test_model_and_risk_window_follow_sidebar(self):
        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                           "reviewed_panel_sha256": sample.csv_hash})
        workspace = DataWorkspace(sample, None, "Synthetic reviewed panel", "No archive")
        with patch("src.workspace_view.load_workspace", return_value=workspace):
            app = AppTest.from_file(str(APP)).run()
            app.selectbox(key="page").set_value("Investment Assistant").run()
            next(s for s in app.selectbox if s.label == "Decision model").set_value("Classroom demonstration").run()
            app.chat_input[0].set_value("What is the maximum feasible return?").run()
            self.assertTrue(any("maximum modeled annual net return is **7.11%**" in item.value for item in app.markdown))
            next(widget for widget in app.selectbox if widget.label == "Decision model").set_value(ETF).run()
            app.chat_input[0].set_value("What is the maximum feasible return?").run()
            self.assertTrue(any("maximum modeled annual net return is **6.65%**" in item.value for item in app.markdown))
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            app.number_input(key="scenario_target").set_value(6.5).run()
            for months in (36, 60):
                next(widget for widget in app.radio if widget.label == "ETF risk window").set_value(months).run()
                app.chat_input[0].set_value("What does the covariance window do?").run()
                expected = build_context(replace(Mandate(), target=.065), ETF, sample, months).active.volatility
                self.assertTrue(any(f"active {months}-month window gives **{expected:.2%}**" in item.value
                                    for item in app.markdown))
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
