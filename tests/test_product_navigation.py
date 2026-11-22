"""BoilerPortfolio entry path and honest development placeholders."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

APP = Path(__file__).resolve().parents[1] / "app.py"


class ProductNavigationTests(CleanCheckout):
    def test_from_infeasible_dashboard_to_custom_builder_and_reset(self):
        app = AppTest.from_file(str(APP)).run()
        self.assertEqual(app.header[0].value, "Investment Overview")
        next(button for button in app.button if button.label == "Explore a custom scenario").click().run()
        self.assertEqual(app.selectbox(key="page").value, "Portfolio Builder")
        self.assertEqual(app.radio(key="scenario_mode").value, "Custom scenario")
        app.number_input(key="scenario_target").set_value(7.50).run()
        app.selectbox(key="page").set_value("Investment Overview").run()
        self.assertTrue(any("REJECT" in item.value for item in app.warning))
        self.assertTrue(any("saved Lab 13 mandate stays fixed" in item.value for item in app.markdown))
        next(button for button in app.button if button.label == "Test portfolio risk").click().run()
        self.assertEqual(app.selectbox(key="page").value, "Risk & Scenario Analysis")
        next(button for button in app.button if button.label == "Reset to default").click().run()
        app.selectbox(key="page").set_value("Committee Decision").run()
        self.assertTrue(any("Annual net objective: **7.00%**" in m.value for m in app.markdown))
        self.assertTrue(any("ILLUSTRATIVE ONLY" in item.value for item in app.markdown))
        self.assertEqual([item.message for item in app.exception], [])

    def test_offline_analyst_and_advanced_search(self):
        app = AppTest.from_file(str(APP)).run()
        app.selectbox(key="page").set_value("Investment Assistant").run()
        self.assertTrue(any("Deterministic" in item.value for item in app.caption))
        app.chat_input[0].set_value("Why a paper pilot?").run()
        self.assertTrue(any("ILLUSTRATIVE ONLY" in item.value for item in app.markdown))
        self.assertEqual(len(app.chat_input), 1)
        self.assertEqual([item.message for item in app.exception], [])
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Research and data").run()
        app.selectbox(key="research_topic").set_value("Security Search").run()
        self.assertTrue(any(item.label == "Ticker" for item in app.text_input))
        self.assertFalse(app.dataframe)
        self.assertEqual([item.message for item in app.exception], [])
