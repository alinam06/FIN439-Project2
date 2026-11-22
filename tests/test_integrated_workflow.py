"""Credential-free user journeys and independent financial reconciliations."""

import json
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.data_workspace import DataWorkspace
from src.investment_context import CLASSROOM, ETF, build_context, entered_weights
from src.portfolio import Mandate
from src.presentation import PAGES
from src.stress import assess_stress, experiment_record, preset
from src.stress_report import replay_bytes
from test_etf_portfolio import reviewed_fixture

APP = Path(__file__).resolve().parents[1] / "app.py"


def widget(items, label):
    return next(item for item in items if item.label == label)


class IntegratedWorkflowTests(CleanCheckout):
    def check(self, app):
        self.assertEqual([item.message for item in app.exception], [])
        self.assertEqual([item.value for item in app.error], [])

    def test_manual_weights_reconcile_and_export_replays(self):
        weights = entered_weights((100, 0, 0, 0, 0))
        context = build_context(Mandate(), weights=weights)
        self.assertEqual(context.model, CLASSROOM)
        self.assertAlmostEqual(context.active.net_return, .035 - .0015)
        self.assertAlmostEqual(context.active.volatility, .005)
        self.assertEqual(context.exposure(weights), (0.0, 1.0))
        self.assertEqual(context.active.verdict, "Fail")
        for invalid in ((100, 1, 0), (101, -1, 0), (float("nan"), 100, 0)):
            with self.assertRaises(ValueError):
                entered_weights(invalid)
        label = "Higher investment costs"
        inputs, mandate = preset(label, context.mandate)
        result = assess_stress(context.mandate, mandate, inputs, active=context.active)
        self.assertAlmostEqual(result.held.net_return, .035 - .0025)
        record = experiment_record(label, context.mandate, mandate, inputs, result, active=context.active)
        self.assertEqual(replay_bytes(json.dumps(record).encode()), record)

    def test_offline_allocation_flows_to_lab_analyst_and_committee(self):
        with patch("socket.getaddrinfo", side_effect=AssertionError("Unexpected provider lookup")):
            app = AppTest.from_file(str(APP)).run()
            self.assertEqual(tuple(app.selectbox(key="page").options), PAGES)
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            self.assertEqual(app.multiselect[0].value, ["BIL", "IEF", "LQD", "VT"])
            app.multiselect[0].set_value(["BIL", "VT"]).run()
            self.assertEqual(next(frame.value for frame in app.dataframe if "ETF candidate" in frame.value)["ETF candidate"].tolist(), ["BIL", "VT"])
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Allocation").run()
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            weights = [item for item in app.number_input if item.key.startswith("custom_mix_")]
            for index, item in enumerate(weights):
                item.set_value(100.0 if index == 0 else 0.0)
            widget(app.button, "Apply allocation").click().run()
            self.check(app)
            self.assertEqual(widget(app.metric, "Net annual return").value, "3.35%")
            widget(app.number_input, weights[0].label).set_value(99.0)
            widget(app.button, "Apply allocation").click().run()
            self.assertTrue(any("total exactly 100%" in item.value for item in app.error))
            self.assertEqual(widget(app.metric, "Net annual return").value, "3.35%")
            app.selectbox(key="page").set_value("Investment Overview").run()
            self.assertTrue(any("Active mix: 3.35%" in c.value for c in app.caption))
            self.assertTrue(any("REJECT" in item.value for item in app.warning))
            app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
            app.selectbox(key="stress_preset").set_value("Higher investment costs").run()
            self.assertEqual(app.dataframe[1].value.iloc[1]["Annual net return"], "3.25%")
            self.check(app)
            app.selectbox(key="page").set_value("Investment Assistant").run()
            app.chat_input[0].set_value("Why was my portfolio rejected?").run()
            self.assertTrue(any("REJECT" in item.value for item in app.markdown))
            app.chat_input[0].set_value(
                "How does diversification affect risk?").run()
            self.assertTrue(any("0.50% volatility" in item.value for item in app.markdown))
            app.chat_input[0].set_value(
                "What happens in an adverse return scenario?").run()
            self.assertTrue(any("Higher investment costs" in item.value and "3.25%" in item.value
                                for item in app.markdown))
            app.selectbox(key="page").set_value("Committee Decision").run()
            self.assertTrue(any("| Custom allocation | 3.35% |" in item.value for item in app.markdown))
            self.assertTrue(app.get("download_button"))
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Allocation").run()
            widget(app.button, "Use constrained optimum").click().run()
            self.assertEqual(widget(app.metric, "Net annual return").value, "7.00%")
            widget(app.button, "Reset to default").click().run()
            self.assertEqual(app.radio(key="scenario_mode").value, "Default client")
            self.check(app)

    def test_reviewed_mode_window_retains_weights_and_updates_risk(self):
        from dataclasses import replace

        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                           "reviewed_panel_sha256": sample.csv_hash})
        workspace = DataWorkspace(sample, None, "Synthetic reviewed panel", "No signal archive")
        with patch("src.workspace_view.load_workspace", return_value=workspace):
            app = AppTest.from_file(str(APP)).run()
            self.assertEqual(widget(app.selectbox, "Decision model").value, ETF)
            widget(app.selectbox, "Decision model").set_value(ETF).run()
            self.assertEqual(widget(app.metric, "Net ceiling").value, "6.65%")
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Allocation").run()
            widget(app.button, "Load equal weights").click().run()
            for months in (36, 60):
                widget(app.radio, "ETF risk window").set_value(months).run()
                self.check(app)
                covariance = sample.returns.tail(months).cov().to_numpy() * 12
                expected_vol = (.25 ** 2 * covariance.sum()) ** .5
                self.assertEqual(widget(app.metric, "Annual volatility").value, f"{expected_vol:.2%}")
            app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
            app.selectbox(key="lab_topic").set_value("Historical performance").run()
            self.assertEqual(len(app.get("vega_lite_chart")), 4)
            self.check(app)
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            self.assertEqual(len(app.get("vega_lite_chart")), 4)
            self.check(app)
