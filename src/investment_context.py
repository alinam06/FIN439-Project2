"""One active mandate, portfolio and risk model for the investment workflow."""

from dataclasses import dataclass, replace

import numpy as np

from src import portfolio
from src.assumptions import ANNUAL_COST, ASSETS, CORRELATIONS
from src.etf_decision_view import decision_case, etf_candidate
from src.etf_evidence import FORWARD
from src.etf_portfolio import BONDS, RESERVE, analyze_windows, etf_frontier, evaluate_etf, snapshot_date
from src.historical import TICKERS

CLASSROOM = "Classroom demonstration"
ETF = "Reviewed ETF snapshot"


@dataclass(frozen=True)
class InvestmentContext:
    mandate: portfolio.Mandate
    model: str
    asset_names: tuple
    gross_returns: tuple
    risk: object
    analysis: portfolio.Analysis
    active: portfolio.Portfolio | None
    sample: object = None
    windows: tuple = ()
    window: int = 60
    annual_cost: float = ANNUAL_COST

    @property
    def optimized(self):
        return self.analysis.portfolios[2] if len(self.analysis.portfolios) == 3 else None

    @property
    def proposal(self):
        """Keep the two baselines while evaluating the selected proposal."""
        if self.active is None:
            return self.analysis
        return replace(self.analysis, portfolios=self.analysis.portfolios[:2] + (self.active,))

    def exposure(self, weights):
        bonds, reserve = ((BONDS, RESERVE) if self.model == ETF else (portfolio.BONDS, portfolio.RESERVE))
        return float(bonds @ weights), float(reserve @ weights)

    def evaluate(self, weights, name="Custom allocation"):
        if self.model == ETF:
            case = evaluate_etf(weights, self.mandate, self.gross_returns, self.annual_cost, self.risk)
            return etf_candidate(name, case, self.mandate)
        return portfolio.evaluate(name, weights, self.mandate, self.risk,
                                  gross_returns=self.gross_returns, annual_cost=self.annual_cost)


def build_context(mandate, model=CLASSROOM, sample=None, window=60, weights=None, *, etf_annual_cost=ANNUAL_COST):
    if model == ETF:
        windows = analyze_windows(sample, mandate, snapshot_date(sample), FORWARD, etf_annual_cost, reviewed=True)
        short, full = windows
        selected = short if window == 36 else full
        risk = np.asarray(selected.annual_covariance)
        frontier = etf_frontier(mandate, FORWARD, etf_annual_cost, risk, selected.max_net_return)
        analysis = replace(decision_case(selected, mandate), frontier=frontier)
        context = InvestmentContext(mandate, model, TICKERS, FORWARD, risk, analysis, None, sample, windows, window, annual_cost=etf_annual_cost)
    else:
        gross = tuple(asset.gross_return for asset in ASSETS)
        risk = portfolio.covariance(tuple(asset.volatility for asset in ASSETS), CORRELATIONS)
        context = InvestmentContext(mandate, CLASSROOM, tuple(asset.name for asset in ASSETS), gross,
                                    risk, portfolio.analyze(mandate), None)
    active = context.evaluate(weights) if weights is not None else context.optimized
    return replace(context, active=active)


def entered_weights(percentages):
    if abs(sum(percentages) - 100) > 1e-7 or not all(0 <= weight <= 100 for weight in percentages):
        raise ValueError("Enter nonnegative weights that total exactly 100%.")
    return tuple(weight / 100 for weight in percentages)
