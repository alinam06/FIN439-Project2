"""Check chart geometry and comparison values using the validated default cases."""

from pathlib import Path

from src.allocation_view import allocation_chart, allocation_rows, baseline_tradeoff, comparison_rows
from src.data_workspace import load_workspace
from src.investment_context import ETF, build_context
from src.portfolio import Mandate
import unittest


class AllocationViewTests(unittest.TestCase):
    def test_weight_and_dollar_bars_reserve_distinct_bands_and_list_all_assets(self):
        context = build_context(Mandate())
        rows = allocation_rows(context, context.analysis.portfolios)
        for dollars, unit, endpoint in ((False, "weight", 1), (True, "dollars", 5_000_000)):
            with self.subTest(unit=unit):
                spec = allocation_chart(rows, context.asset_names, context.mandate.portfolio_value, dollars).to_dict()
                self.assertEqual(spec["mark"]["orient"], "horizontal")
                self.assertGreater(spec["height"]["step"], spec["mark"]["size"])
                self.assertEqual(spec["encoding"]["x2"]["field"], f"End {unit}")
                self.assertEqual(spec["encoding"]["color"]["scale"]["domain"], list(context.asset_names))
                for _, segments in rows.groupby("Portfolio"):
                    self.assertAlmostEqual(segments[f"End {unit}"].iloc[-1], endpoint)
        for portfolio in context.analysis.portfolios:
            contributions = rows.loc[rows["Portfolio"] == portfolio.name, "Volatility contribution"]
            self.assertAlmostEqual(contributions.sum(), portfolio.volatility)

    def test_etf_infeasibility_adds_status_row_with_no_fabricated_weights(self):
        sample = load_workspace(Path(__file__).resolve().parents[1] / "data").etf
        if sample is None:
            # The default-classroom geometry test runs on a public checkout.
            # A synthetic fixture supports the same already-tested default ETF objective.
            from test_etf_portfolio import reviewed_fixture
            sample = reviewed_fixture()
        context = build_context(Mandate(), ETF, sample)
        rows = allocation_rows(context, context.analysis.portfolios)
        self.assertEqual(rows["Portfolio"].nunique(), 2)
        table = comparison_rows(context, context.analysis.portfolios, rows)
        self.assertEqual(table.iloc[-1]["Overall verdict"], "No feasible solution")
        self.assertEqual(table.iloc[-1]["Expected annual net return"], "—")
        self.assertTrue(all(table.iloc[i]["Modeled failures"] != "None" for i in (0, 1)))
        self.assertIn("Both baselines fail", baseline_tradeoff(context))
