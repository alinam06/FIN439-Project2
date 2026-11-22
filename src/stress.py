"""Hypothetical sensitivities using the validated classroom optimizer."""

from dataclasses import asdict, dataclass, replace
import math

import numpy as np

from src.assumptions import ANNUAL_COST, ASSETS, CORRELATIONS
from src.portfolio import Analysis, Mandate, Portfolio, analyze, covariance, evaluate


@dataclass(frozen=True)
class StressInputs:
    equity_shift: float = 0.0
    bond_shift: float = 0.0
    cash_shift: float = 0.0
    equity_vol_scale: float = 1.0
    bond_vol_scale: float = 1.0
    cash_vol_scale: float = 1.0
    equity_bond_corr: float = CORRELATIONS[2][3]
    treasury_bond_corr: float = CORRELATIONS[1][2]
    equity_company_corr: float = CORRELATIONS[3][4]
    annual_cost: float = ANNUAL_COST
    trade_cost: float = 0.0

    def model_inputs(self):
        shifts = (self.cash_shift, self.bond_shift, self.bond_shift, self.equity_shift, self.equity_shift)
        scales = (self.cash_vol_scale, self.bond_vol_scale, self.bond_vol_scale,
                  self.equity_vol_scale, self.equity_vol_scale)
        gross = tuple(asset.gross_return + shift for asset, shift in zip(ASSETS, shifts))
        volatility = tuple(asset.volatility * scale for asset, scale in zip(ASSETS, scales))
        if (not all(math.isfinite(value) and -1 < value <= 1 for value in gross)
            or not all(math.isfinite(value) and 0 <= value <= 1
                       for value in (self.annual_cost, self.trade_cost))):
            raise ValueError("Check return and cost inputs. Returns must be above −100% and at most 100%, "
                             "and costs must be between 0% and 100%.")
        correlation = np.array(CORRELATIONS)
        for i, j, value in ((2, 3, self.equity_bond_corr), (1, 2, self.treasury_bond_corr),
                            (3, 4, self.equity_company_corr)):
            correlation[i, j] = correlation[j, i] = value
        risk = covariance(volatility, correlation)
        try:
            np.linalg.cholesky(risk)
        except np.linalg.LinAlgError as error:
            raise ValueError("Stress optimization requires positive-definite covariance.") from error
        return gross, volatility, correlation, risk


@dataclass(frozen=True)
class StressResult:
    base: Analysis
    stressed: Analysis
    held: Portfolio | None
    candidate: Portfolio | None
    traded_share: float | None
    trade_drag: float | None


PRESETS = {
    "Base case": "Active mandate and original classroom assumptions.",
    "Equity market deterioration": "Equity expected returns −2 percentage points and equity volatilities ×1.25.",
    "Higher investment costs": "Annual expenses rise from 15 to 25 bp. One-time cost is 25 bp per dollar traded.",
    "Rising stock/bond correlation": "Global equity and investment-grade fund correlation rises from 0.25 to 0.40.",
    "Increased liquidity requirement": "Reserve floor rises by 5 percentage points, capped at 100%.",
    "Combined adverse scenario": "Equity returns −2 pp, bond returns −0.5 pp, cash proxy −0.25 pp, "
                                 "equity volatility ×1.25, bond volatility ×1.15, stock/bond correlation 0.40, "
                                 "annual expenses 35 bp, trading cost 25 bp, reserve floor +5 pp.",
}


def preset(name, base):
    inputs = StressInputs()
    if name == "Equity market deterioration":
        inputs = replace(inputs, equity_shift=-.02, equity_vol_scale=1.25)
    elif name == "Higher investment costs":
        inputs = replace(inputs, annual_cost=.0025, trade_cost=.0025)
    elif name == "Rising stock/bond correlation":
        inputs = replace(inputs, equity_bond_corr=.40)
    elif name == "Combined adverse scenario":
        inputs = replace(inputs, equity_shift=-.02, bond_shift=-.005, cash_shift=-.0025,
                         equity_vol_scale=1.25, bond_vol_scale=1.15, equity_bond_corr=.40,
                         annual_cost=.0035, trade_cost=.0025)
    if name in ("Increased liquidity requirement", "Combined adverse scenario"):
        return inputs, replace(base, min_reserve=min(1.0, base.min_reserve + .05))
    return inputs, base


def candidate(analysis):
    return analysis.portfolios[2] if len(analysis.portfolios) == 3 else None


def assess_stress(base_mandate, stressed_mandate, inputs, *, active=None):
    gross, volatility, correlation, risk = inputs.model_inputs()
    base = analyze(base_mandate, frontier_points=0)
    if active is not None:
        base = replace(base, portfolios=base.portfolios[:2] + (active,))
    original = candidate(base)
    stressed = analyze(stressed_mandate, frontier_points=0, gross_returns=gross,
                       volatilities=volatility, correlations=correlation, annual_cost=inputs.annual_cost)
    proposed = candidate(stressed)
    held = (evaluate("Original weights under stress", original.weights, stressed_mandate, risk,
                     gross_returns=gross, annual_cost=inputs.annual_cost) if original else None)
    traded = (sum(abs(new - old) for old, new in zip(original.weights, proposed.weights))
              if original and proposed else None)
    return StressResult(base, stressed, held, proposed, traded,
                        None if traded is None else traded * inputs.trade_cost)


def decision(analysis):
    if candidate(analysis) is None:
        return "Defer", analysis.decision
    if candidate(analysis).verdict == "Fail":
        failed = ", ".join(rule.name for rule in candidate(analysis).rules if rule.status == "Fail")
        return "Reject", f"Active allocation fails: {failed}."
    return "Due diligence", analysis.decision


def held_decision(held):
    if held is None:
        return "Unavailable. The base scenario has no optimized portfolio to hold."
    hard_failures = [rule.name for rule in held.rules if rule.status == "Fail"
                     and rule.name != "Expected net return objective"]
    if hard_failures:
        return "Reject original weights under the stressed mandate: " + ", ".join(hard_failures) + "."
    if any(rule.status == "Fail" for rule in held.rules):
        return "Defer use of the original weights. Their stressed expected net return misses the target."
    return "Continue due diligence on the original weights. Mandatory evidence and loss tolerance remain unresolved."


def experiment_record(label, base, stressed, inputs, result, *, active=None):
    """Serializable assumptions and calculated outcomes for a later replay."""
    record = {"schema_version": 1, "scenario": label, "base_mandate": asdict(base), "stressed_mandate": asdict(stressed),
            "inputs": asdict(inputs), "results": asdict(result),
            "decisions": {"base": decision(result.base), "stressed": decision(result.stressed),
                          "hold": held_decision(result.held)}}
    if active is not None:
        record["active_weights"] = list(active.weights)
    return record


def historical_windows(sample=None, *, reviewed=False):
    if sample is None:
        return "Unavailable. Supply an aligned ETF price panel and source metadata.", {}
    if not reviewed or len(sample.returns) < 60:
        return "Unavailable. Both windows require a reviewed panel with 60 aligned monthly returns.", {}
    windows = {}
    for months in (36, 60):
        returns = sample.returns.tail(months)
        windows[months] = (returns.index[0].date(), returns.index[-1].date(),
                           returns.std(ddof=1) * np.sqrt(12), returns.cov() * 12, returns.corr())
    return "Retrospective estimates from the reviewed upload.", windows
