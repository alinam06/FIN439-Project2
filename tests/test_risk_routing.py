"""Regression coverage for the reported one-argument classroom renderer."""

from pathlib import Path
from unittest.mock import patch

import pyarrow.ipc
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.presentation import PAGES
from src.stress_view import stress_view as classroom_renderer

APP = Path(__file__).resolve().parents[1] / "app.py"


def stress_view(mandate):
    return classroom_renderer(mandate)


class RiskRoutingTests(CleanCheckout):
    def test_classroom_renderer_receives_only_the_mandate(self):
        with patch("src.stress_view.stress_view", new=stress_view):
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
        self.assertEqual([item.message for item in app.exception], [])
        self.assertTrue(any(item.label == "Stress scenario" for item in app.selectbox))
        self.assertTrue(any("Unavailable" in item.value for item in app.info))


class NavigationTests(CleanCheckout):
    def assert_no_exceptions(self, app, page):
        self.assertEqual([item.message for item in app.exception], [], page)
        self.assertEqual([item.value for item in app.error], [], page)

    def test_all_sections_in_both_models_with_custom_controls_and_reset(self):
        from dataclasses import replace

        from src.data_workspace import DataWorkspace
        from test_etf_portfolio import reviewed_fixture

        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                          "reviewed_panel_sha256": sample.csv_hash})
        workspace = DataWorkspace(sample, None, "Synthetic reviewed fixture", "Missing archive.")
        with patch("src.workspace_view.load_workspace", return_value=workspace):
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            for mode in ("Reviewed ETF snapshot", "Classroom demonstration"):
                with self.subTest(model=mode):
                    self.select_model(app, mode)
                    self.walk(app, PAGES, mode, "7.00%")
                    app.radio(key="scenario_mode").set_value("Custom scenario").run()
                    app.number_input(key="scenario_target").set_value(6.5).run()
                    self.walk(app, PAGES, mode, "6.50%")
                    next(button for button in app.button if button.label == "Reset to default").click().run()
                    self.walk(app, PAGES, mode, "7.00%")

    def select_model(self, app, mode):
        next(widget for widget in app.selectbox if widget.label == "Decision model").set_value(mode).run()

    def walk(self, app, pages, mode, target):
        for page in pages:
            with self.subTest(page=page, model=mode, target=target):
                app.selectbox(key="page").set_value(page).run()
                self.assert_no_exceptions(app, page)
                self.assertEqual(f"{float(app.number_input(key='scenario_target').value):.2f}%"
                                 if app.radio(key="scenario_mode").value == "Custom scenario"
                                 else "7.00%", target)
                if page == "Investment Overview":
                    self.assertEqual(app.metric[0].value, target)
                    self.assertEqual(app.metric[1].value, "6.65%" if mode == "Reviewed ETF snapshot" else "7.11%")
                if page == "Risk & Scenario Analysis":
                    app.selectbox(key="lab_topic").set_value("Risk and allocation comparison").run()
                    if mode == "Reviewed ETF snapshot":
                        self.assertIn("VT", app.dataframe[0].value.columns)
                        self.assertNotIn("Fictional", str(app.dataframe[0].value))
                        self.assertEqual(len(app.dataframe[0].value), 6 if target == "6.50%" else 4)
                    else:
                        next(widget for widget in app.radio if widget.label == "Allocation display"
                             ).set_value("Dollar amounts").run()
                        self.assert_no_exceptions(app, page)
                        chart = app.get("vega_lite_chart")[1].proto
                        rows = pyarrow.ipc.open_stream(chart.datasets[0].data.data).read_all().to_pandas()
                        self.assertEqual(rows.loc[rows["Portfolio"] == "Equal weight", "Dollars"].iloc[0], 1_000_000)
                if page == "Risk & Scenario Analysis":
                    app.selectbox(key="lab_topic").set_value("Stress testing").run()
                    if mode == "Reviewed ETF snapshot":
                        app.number_input(key="etf_risk_shock").set_value(0.0).run()
                        self.assertEqual(set(app.dataframe[0].value["Modeled maximum"]), {"6.65%"})
                        app.number_input(key="etf_risk_shock").set_value(1.0).run()
                        self.assert_no_exceptions(app, page)
                        self.assertEqual(set(app.dataframe[1].value["Net target"]), {target})
                        self.assertEqual(set(app.dataframe[0].value["Modeled maximum"]), {"6.65%", "5.81%"})
                        expected = "HOLD" if target == "6.50%" else "REJECT"
                        self.assertEqual(app.dataframe[0].value["Committee action"].tolist(), [expected, "REJECT"])
                    else:
                        app.selectbox(key="stress_preset").set_value("Higher investment costs").run()
                        self.assert_no_exceptions(app, page)
                        self.assertEqual(set(app.dataframe[2].value["Net target"]), {target})
                        self.assertTrue(any("Retrospective estimates" in item.value for item in app.info))
                if page == "Portfolio Builder":
                    app.selectbox(key="builder_view").set_value("Research and data").run()
                    for topic in ("Historical Market Data", "Economic Signals", "Security Search"):
                        app.selectbox(key="research_topic").set_value(topic).run()
                        self.assert_no_exceptions(app, topic)
                        if topic == "Economic Signals":
                            self.assertTrue(any("Signal unavailable" in item.value for item in app.warning))
                    app.selectbox(key="builder_view").set_value("Allocation").run()
                if page == "Committee Decision":
                    for topic in ("Data sources and tests", "Experiment replay", "Mandate and methodology"):
                        app.selectbox(key="validation_topic").set_value(topic).run()
                        self.assert_no_exceptions(app, topic)
                    app.selectbox(key="validation_topic").set_value("Decision summary").run()
                    self.assertTrue(any(f"Annual net objective: **{target}**" in m.value for m in app.markdown))

    def test_all_sections_fall_back_without_local_data(self):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        for page in app.selectbox(key="page").options:
            with self.subTest(page=page):
                app.selectbox(key="page").set_value(page).run()
                self.assert_no_exceptions(app, page)
                self.assertFalse(any(widget.label == "Decision model" for widget in app.selectbox))
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Research and data").run()
        app.selectbox(key="research_topic").set_value("Historical Market Data").run()
        self.assertTrue(any("Missing from data/" in item.value for item in app.info))
        self.assert_no_exceptions(app, "Missing-data historical research")
