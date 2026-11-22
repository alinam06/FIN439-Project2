"""Verify cost plumbing without solving a new financial scenario."""

from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.assumptions import ANNUAL_COST
from src.data_workspace import DataWorkspace
from src.investment_context import ETF, build_context
from src.portfolio import Mandate
from test_etf_portfolio import reviewed_fixture

APP = Path(__file__).resolve().parents[1] / "app.py"


class EtfCostControlTests(unittest.TestCase):
    def test_context_passes_cost_to_existing_engine_without_running_it(self):
        sample = reviewed_fixture()
        mandate = Mandate()
        existing = build_context(mandate, ETF, sample)
        fee = ANNUAL_COST + .0001
        with (patch("src.investment_context.analyze_windows", return_value=existing.windows) as solver,
              patch("src.investment_context.etf_frontier", return_value=()) as frontier):
            context = build_context(mandate, ETF, sample, etf_annual_cost=fee)
        self.assertEqual(solver.call_args.args[4], fee)
        self.assertEqual(frontier.call_args.args[2], fee)
        self.assertEqual(context.annual_cost, fee)
        self.assertEqual(context.mandate, mandate)

    def test_builder_fee_persists_and_reset_restores_default_with_solver_stubbed(self):
        sample = reviewed_fixture()
        sample = replace(sample, metadata={**sample.metadata, "provider": "Alpha Vantage",
                                           "reviewed_panel_sha256": sample.csv_hash})
        mandate = Mandate()
        baseline = build_context(mandate, ETF, sample)
        workspace = DataWorkspace(sample, None, "Synthetic reviewed panel", "No archive")
        with (patch("src.workspace_view.load_workspace", return_value=workspace),
              patch("src.investment_context.build_context", return_value=baseline) as engine):
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            self.assertEqual(app.number_input(key="scenario_etf_cost_bp").value, ANNUAL_COST * 10000)
            app.number_input(key="scenario_etf_cost_bp").set_value(ANNUAL_COST * 10000 + 1).run()
            self.assertAlmostEqual(engine.call_args.kwargs["etf_annual_cost"], ANNUAL_COST + .0001)
            app.selectbox(key="page").set_value("Investment Overview").run()
            self.assertAlmostEqual(engine.call_args.kwargs["etf_annual_cost"], ANNUAL_COST + .0001)
            next(button for button in app.button if button.label == "Reset to default").click().run()
            self.assertEqual(engine.call_args.kwargs["etf_annual_cost"], ANNUAL_COST)
            self.assertEqual(engine.call_args.args[0], mandate)
            self.assertFalse(app.exception)
