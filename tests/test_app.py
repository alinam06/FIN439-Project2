from pathlib import Path
from unittest.mock import patch

import pyarrow.ipc
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout


class DashboardTests(CleanCheckout):
    def test_default_and_custom_inputs_recalculate(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("$5M" in c.value for c in app.caption))
        self.assertEqual(len(app.metric), 4)
        self.assertEqual(app.metric[1].value, "7.11%")
        self.assertFalse(app.dataframe)
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Allocation").run()
        self.assertTrue(any(len(d.value) == 3 and "Expected annual net return" in d.value for d in app.dataframe))
        app.selectbox(key="page").set_value("Investment Overview").run()

        app.sidebar.radio[0].set_value("Custom scenario").run()
        inputs = {widget.label: widget for widget in app.sidebar.number_input}
        inputs["Portfolio value ($)"].set_value(2_000_000.0)
        inputs["Investment horizon (years)"].set_value(10)
        inputs["Annual net return target (%)"].set_value(7.50)
        inputs["Minimum liquid reserve (%)"].set_value(15.0)
        inputs["Minimum five-day redeemable share (%)"].set_value(95.0)
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(any("$2M · 10 years" in c.value for c in app.caption))
        self.assertIn("Defer", app.warning[0].value)
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Allocation").run()
        target = next(m for m in app.metric if m.label == "Target value in 10 years")
        self.assertEqual(target.value, f"${2_000_000 * 1.075 ** 10:,.0f}")
        self.assertTrue(any("Overall verdict" in d.value and "No feasible solution" in d.value["Overall verdict"].tolist()
                            for d in app.dataframe))
        app.sidebar.selectbox[0].set_value("Committee Decision").run()
        app.selectbox(key="validation_topic").set_value("Mandate and methodology").run()
        checks = app.dataframe[0].value
        redemption = checks[checks["Rule"] == "Redeemable within five business days"]
        self.assertTrue(redemption["Evidence"].str.contains("95.00%").all())
        self.assertTrue((redemption["Status"] == "Unverified").all())
        app.sidebar.selectbox[0].set_value("Risk & Scenario Analysis").run()
        app.selectbox(key="lab_topic").set_value("Risk and allocation comparison").run()
        next(radio for radio in app.radio if radio.label == "Allocation display").set_value("Dollar amounts").run()
        chart = app.get("vega_lite_chart")[1].proto
        rows = pyarrow.ipc.open_stream(chart.datasets[0].data.data).read_all().to_pandas()
        self.assertEqual(rows.loc[rows["Portfolio"] == "Equal weight", "Dollars"].iloc[0], 400_000)

    def test_custom_caps_change_ceiling_and_reset_to_default(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        app.sidebar.radio[0].set_value("Custom scenario").run()
        inputs = {widget.label: widget for widget in app.sidebar.number_input}
        inputs["Maximum individual company (%)"].set_value(0.0).run()
        self.assertEqual(app.metric[1].value, "7.03%")
        inputs = {widget.label: widget for widget in app.sidebar.number_input}
        inputs["Minimum investment-grade bonds (%)"].set_value(50.0).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, "6.28%")
        self.assertFalse(any("Active mix:" in c.value for c in app.caption))
        app.sidebar.radio[0].set_value("Default client").run()
        self.assertEqual(app.metric[1].value, "7.11%")
        self.assertIn("Age 45 · Retirement at 60", [element.value for element in app.sidebar.markdown])

    def test_invalid_analysis_shows_controlled_error(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        with patch("src.portfolio.analyze", side_effect=ValueError("Invalid risk inputs.")):
            app = AppTest.from_file(str(path)).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.error[0].value, "Analysis unavailable. Invalid risk inputs.")

    def test_overview_reports_headroom_and_displays_infeasibility(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Margin"], "+11 bp")
        self.assertTrue(any("12.10% annual volatility · Mandate Unverified" in c.value for c in app.caption))
        app.sidebar.radio[0].set_value("Custom scenario").run()
        next(widget for widget in app.sidebar.number_input
             if widget.label == "Annual net return target (%)").set_value(7.5).run()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Margin"], "-39 bp")
        self.assertFalse(any("Active mix:" in c.value for c in app.caption))
        self.assertIn("Defer", app.warning[0].value)

    def test_reset_clears_custom_values_and_stress_page_labels_status(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        app.sidebar.radio[0].set_value("Custom scenario").run()
        next(widget for widget in app.sidebar.number_input
             if widget.label == "Portfolio value ($)").set_value(2_000_000.0).run()
        app.sidebar.selectbox[0].set_value("Risk & Scenario Analysis").run()
        app.selectbox(key="lab_topic").set_value("Risk and allocation comparison").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("vega_lite_chart")), 2)
        next(button for button in app.sidebar.button if button.label == "Reset to default").click().run()
        self.assertEqual(app.sidebar.radio[0].value, "Default client")
        app.sidebar.radio[0].set_value("Custom scenario").run()
        self.assertEqual(next(widget.value for widget in app.sidebar.number_input
                              if widget.label == "Portfolio value ($)"), 5_000_000.0)
        app.sidebar.selectbox[0].set_value("Risk & Scenario Analysis").run()
        app.selectbox(key="lab_topic").set_value("Stress testing").run()
        self.assertTrue(any("Unavailable" in item.value for item in app.info))
        self.assertTrue(any(item.label == "Stress scenario" for item in app.selectbox))
        self.assertFalse(app.exception)
