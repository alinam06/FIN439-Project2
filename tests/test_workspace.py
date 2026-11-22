"""Consolidated workflow and data-source regression checks."""

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

from src.committee import ACTIONS, recommendation, weight_ranges
from src.data_workspace import ETF_FILES, SIGNAL_FILES, load_workspace
from src.economic_signal import Signal
from src.portfolio import Mandate, analyze
from test_economic_signal import encode as encode_signal, fixture as signal_fixture
from test_historical import encode, fixture


class DataWorkspaceTests(unittest.TestCase):
    def test_missing_and_partial_data_remain_explicit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ETF_FILES[0]).write_text("partial")
            workspace = load_workspace(root)
        self.assertIsNone(workspace.etf)
        self.assertIsNone(workspace.archive)
        self.assertIn(ETF_FILES[1], workspace.etf_status)
        self.assertIn(SIGNAL_FILES[0], workspace.signal_status)

    def test_automatic_repository_load_and_session_override_does_not_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            prices, metadata = fixture()
            files = dict(zip((*ETF_FILES, *SIGNAL_FILES), (encode(prices), metadata, *encode_signal(signal_fixture()))))
            for name, contents in files.items():
                (root / name).write_bytes(contents)
            workspace = load_workspace(root)
            self.assertEqual(len(workspace.etf.returns), 60)
            self.assertIsNotNone(workspace.archive)
            self.assertIn("Repository data/", workspace.etf_status)
            override = load_workspace(root, etf_override=(b"invalid", metadata))
            self.assertIsNone(override.etf)
            self.assertIn("Session upload rejected", override.etf_status)
            self.assertEqual({path.name: path.read_bytes() for path in root.iterdir()}, files)


class CommitteeTests(unittest.TestCase):
    def test_actions_never_grant_live_approval(self):
        base = analyze(Mandate(), frontier_points=0)
        for action in ACTIONS:
            with self.subTest(action=action):
                decision = recommendation(base, requested=action)
                self.assertEqual(decision.action, "REJECT" if action == "REJECT" else "HOLD")
                self.assertTrue(any("0%" in stop for stop in decision.stops))
        self.assertIn("Defer ALLOCATE TO", recommendation(base, requested="ALLOCATE TO").ask)
        stressed = analyze(Mandate(target=.075), frontier_points=0)
        self.assertEqual(recommendation(stressed).action, "REJECT")

    def test_signal_changes_monitoring_and_ranges_contain_candidate(self):
        mandate = Mandate()
        base = analyze(mandate, frontier_points=0)
        decision = recommendation(base, Signal("Review", "Widening"))
        self.assertEqual(decision.action, "HOLD")
        self.assertTrue(any("widening" in trigger for trigger in decision.triggers))
        for weight, (low, high) in zip(base.portfolios[2].weights, weight_ranges(mandate)):
            self.assertLessEqual(low, weight + 1e-9)
            self.assertLessEqual(weight, high + 1e-9)
        self.assertFalse(weight_ranges(replace(mandate, target=.075)))


class ConsolidationUITests(CleanCheckout):
    def test_offline_default_and_scenario_follow_navigation(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        with patch("socket.getaddrinfo", side_effect=AssertionError("Unexpected DNS request")):
            app = AppTest.from_file(str(path)).run()
            self.assertFalse(app.exception)
            self.assertFalse(app.get("file_uploader"))
            self.assertEqual(app.metric[1].value, "7.11%")
            self.assertTrue(any("ILLUSTRATIVE ONLY" in item.value for item in app.markdown))
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Allocation").run()
            app.radio(key="scenario_mode").set_value("Custom scenario").run()
            app.number_input(key="scenario_target").set_value(7.5).run()
            app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
            app.selectbox(key="lab_topic").set_value("Risk and allocation comparison").run()
            self.assertEqual(app.dataframe[0].value["Overall verdict"].iloc[-1], "No feasible solution")
            app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
            app.selectbox(key="lab_topic").set_value("Stress testing").run()
            self.assertTrue(all(value == "7.50%" for value in app.dataframe[0].value["Net target"]))
            app.selectbox(key="page").set_value("Investment Overview").run()
            self.assertTrue(any("REJECT" in item.value for item in app.warning))
            self.assertFalse(app.exception)

    def test_repository_etf_is_shared_by_research_and_risk(self):
        prices, metadata = fixture()
        path = Path(__file__).resolve().parents[1] / "app.py"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ETF_FILES[0]).write_bytes(encode(prices))
            (root / ETF_FILES[1]).write_bytes(metadata)
            with patch("src.workspace_view.load_workspace", side_effect=lambda **kwargs: load_workspace(root, **kwargs)):
                app = AppTest.from_file(str(path)).run()
                app.selectbox(key="page").set_value("Portfolio Builder").run()
                app.selectbox(key="builder_view").set_value("Research and data").run()
                app.selectbox(key="research_topic").set_value("Historical Market Data").run()
                self.assertTrue(any("structural checks passed" in item.value for item in app.success))
                self.assertFalse(app.get("file_uploader"))
                next(item for item in app.checkbox if "reconciled" in item.label).check().run()
                app.selectbox(key="page").set_value("Risk & Scenario Analysis").run()
                app.selectbox(key="lab_topic").set_value("Stress testing").run()
                self.assertTrue(any("Retrospective estimates" in item.value for item in app.info))
                self.assertFalse(app.exception)
