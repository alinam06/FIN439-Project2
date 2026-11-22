"""Narrative boundary and single briefing regression checks."""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.briefing import investment_brief, project_etf_finding
from src.data_workspace import DataWorkspace
from src.investment_context import build_context
from src.investment_views import committee_sections, committee_summary
from src.portfolio import Mandate
from test_etf_portfolio import reviewed_fixture

APP = Path(__file__).resolve().parents[1] / "app.py"


class SubmissionBriefTests(CleanCheckout):
    def test_public_report_scopes_pilot_and_separates_current_from_future(self):
        context = build_context(Mandate())
        sections = committee_sections(context, None, "PILOT", "Default", None, investment_brief(context),
                                      etf_note=project_etf_finding())
        exported = committee_summary(sections)
        self.assertEqual(len(sections), 7)
        self.assertEqual(exported.count("## Monitoring"), 1)
        self.assertIn("**ILLUSTRATIVE ONLY**", exported)
        self.assertIn("This session has not reproduced that analysis", exported)
        self.assertIn("Paper-test the evaluation process.", exported)
        self.assertIn("10.00% · At limit | At least 10.00% | Reject weights that breach the limit", exported)
        self.assertIn("Live BAA10Y is unavailable. Dated FRED evidence", exported)
        self.assertIn("Project 2 investment universe is BIL, IEF, LQD, VT", exported)

    def test_reviewed_etf_button_opens_actual_universe_view(self):
        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                           "reviewed_panel_sha256": sample.csv_hash})
        workspace = DataWorkspace(sample, None, "Synthetic reviewed panel", "No archive")
        with patch("src.workspace_view.load_workspace", return_value=workspace):
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            self.assertEqual(app.metric[1].value, "6.65%")
            next(s for s in app.selectbox if s.label == "Decision model").set_value("Classroom demonstration").run()
            self.assertEqual(app.metric[1].value, "7.11%")
            next(btn for btn in app.button if btn.label == "Open reviewed ETF analysis").click().run()
            self.assertEqual(app.metric[1].value, "6.65%")
            app.selectbox(key="page").set_value("Committee Decision").run()
            self.assertFalse(app.exception)
            self.assertTrue(any("**REJECT** the ETF allocation" in item.value and "$0" in item.value
                                for item in app.warning))
            self.assertTrue(any("No candidate to assess" in item.value for item in app.markdown))
