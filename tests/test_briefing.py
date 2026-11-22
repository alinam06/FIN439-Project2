"""Check the committee's reading of the financial engine and screen boundaries."""

from dataclasses import replace
from pathlib import Path

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout
from src.analyst import answer_question
from src.briefing import exclusion_effect, investment_brief, monitoring_rows, scenario_row, stress_finding
from src.committee import decision_for
from src.judgment import StressChallenge
from src.investment_context import build_context
from src.portfolio import Mandate
from src.stress import PRESETS, assess_stress, preset

APP = Path(__file__).resolve().parents[1] / "app.py"


class BriefingTests(CleanCheckout):
    def test_default_findings_and_changed_action_reconcile_to_financial_engine(self):
        context = build_context(Mandate())
        base = investment_brief(context)
        self.assertEqual((base.action, base.capital), ("ILLUSTRATIVE ONLY", 0))
        self.assertEqual(len(base.findings), 3)
        self.assertIn(f"{context.analysis.max_net_return:.2%}", base.findings[0].evidence)
        self.assertIn("91.8%", base.findings[1].evidence)
        self.assertIn("loss tolerance", base.approval_gap)
        self.assertTrue(any("Unavailable" in row for row in monitoring_rows(context)
                            if row[1] == "BAA10Y"))
        cost = next(row for row in monitoring_rows(context) if row[1] == "Recurring annual costs")
        self.assertIn("15.0 bp", cost[3])
        self.assertIn("26.0 bp", cost[3])
        failed = build_context(replace(Mandate(), target=.075))
        brief = investment_brief(failed)
        self.assertEqual((brief.action, brief.capital), ("REJECT", 0))
        self.assertIn("-39.0 bp", brief.findings[0].evidence)
        self.assertIn("**REJECT**", answer_question("Why should we not invest today?", failed, None, "PILOT"))
        without_treasury = exclusion_effect(context, 1)
        self.assertEqual(without_treasury.verdict, "Fail")
        self.assertIsNone(exclusion_effect(context, 0))

    def test_scenario_rows_distinguish_rescue_and_infeasibility(self):
        ctx = build_context(Mandate())
        expected = {
            "Higher investment costs": ("ILLUSTRATIVE ONLY", "6.90%", "7.00%", "Held fails"),
            "Equity market deterioration": ("REJECT", "5.54%", "Unavailable", "No feasible mix"),
            "Rising stock/bond correlation": ("ILLUSTRATIVE ONLY", "7.00%", "7.00%", "higher risk"),
        }
        for label, (action, held, new, effect) in expected.items():
            inputs, mandate = preset(label, ctx.mandate)
            result = assess_stress(ctx.mandate, mandate, inputs)
            row = scenario_row(label, PRESETS[label], ctx, result.stressed, result.held,
                               inputs.trade_cost, None, "PILOT")
            self.assertEqual((row["Committee action"], row["Held net return"], row["Reoptimized net return"]),
                             (action, held, new))
            self.assertIn(effect, row["Investment effect"])

    def test_stress_findings_match_the_size_and_consequence_of_the_shock(self):
        context = build_context(Mandate())
        for name, expected in (
            ("Rising stock/bond correlation", ("+0.14 pp", "little effect", "Keep authorization unchanged")),
            ("Higher investment costs", ("6.90%", "12.58%", "Set aside the held weights")),
            ("Equity market deterioration", ("5.61%", "No modeled allocation", "Stop the proposal")),
        ):
            with self.subTest(name=name):
                inputs, mandate = preset(name, context.mandate)
                result = assess_stress(context.mandate, mandate, inputs)
                challenge = StressChallenge(name, result.stressed, result.held, mandate.target, inputs.trade_cost)
                policy = decision_for(context, analysis=result.stressed)
                finding = stress_finding(context.active, context.analysis.max_net_return,
                                         context.mandate.target, challenge, policy)
                for text in expected:
                    self.assertIn(text, finding)

    def test_distinct_pages_and_same_active_decision(self):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        pages = {
            "Investment Overview": "Next steps",
            "Portfolio Builder": "Compare allocation choices",
            "Risk & Scenario Analysis": "Stress overview",
            "Investment Assistant": "Suggested questions",
            "Committee Decision": "Executive recommendation",
        }
        for page, anchor in pages.items():
            app.selectbox(key="page").set_value(page).run()
            self.assertFalse(app.exception, page)
            labels = {item.value for item in app.subheader} | {item.label for item in app.expander} | {item.value for item in app.caption}
            self.assertEqual(labels.intersection(pages.values()), {anchor}, page)
            if page == "Risk & Scenario Analysis":
                app.selectbox(key="stress_preset").set_value("Higher investment costs").run()
                content = " ".join(m.value for m in app.markdown)
                self.assertIn("Set aside the held weights", content)
                self.assertTrue(any(e.label == "Selected scenario calculations" for e in app.expander))
                self.assertNotIn("Due diligence →", content)
                for obsolete in ("**Base** ·", "**Stressed** ·", "**Hold original weights** ·"):
                    self.assertNotIn(obsolete, content)
                self.assertEqual(app.dataframe[0].value.iloc[0]["Reoptimized net return"], "—")
        app.radio(key="scenario_mode").set_value("Custom scenario").run()
        app.number_input(key="scenario_target").set_value(7.5).run()
        self.assertTrue(any("**REJECT**" in msg.value for msg in app.warning))
        app.selectbox(key="page").set_value("Investment Overview").run()
        self.assertTrue(any("**REJECT**" in msg.value for msg in app.warning))
        app.selectbox(key="page").set_value("Investment Assistant").run()
        app.chat_input[0].set_value("Why should we not invest today?").run()
        self.assertTrue(any("**REJECT**" in msg.value and "$0 live" in msg.value for msg in app.markdown))
        self.assertFalse(app.exception)
