"""Conditional four-ETF analysis using reviewed snapshot risk and explicit return inputs."""

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np

from src.historical import TICKERS
from src.portfolio import TOL, feasible_vertices, minimum_variance, portfolio_metrics

BONDS = np.array([0., 1., 1., 0.])
RESERVE = np.array([1., 0., 0., 0.])
BASELINES = (
    ("Equal weight", (.25, .25, .25, .25)),
    ("60% VT / 40% LQD", (0., 0., .40, .60)),
)


@dataclass(frozen=True)
class ETFCase:
    weights: tuple[float, ...]
    net_return: float
    volatility: float
    modeled_failures: tuple[str, ...]

    @property
    def verdict(self):
        return "Fail" if self.modeled_failures else "Unverified"


@dataclass(frozen=True)
class WindowResult:
    months: int
    first_price_date: date
    last_price_date: date
    annual_covariance: tuple
    max_net_return: float | None
    portfolios: dict[str, ETFCase]
    decision: str


def snapshot_date(sample):
    retrieved = datetime.fromisoformat(sample.metadata["downloaded_at"])
    return retrieved.astimezone(ZoneInfo("America/New_York")).date()


def analyze_windows(sample, mandate, decision_date, gross_returns, cost, *, reviewed=False):
    """Compare two windows using one snapshot and identical forward assumptions."""
    if not reviewed:
        raise ValueError("Review provider, exchange dates and distributions before using this panel.")
    if decision_date != snapshot_date(sample) or decision_date > datetime.now(ZoneInfo("America/New_York")).date():
        raise ValueError("Use the evidenced capture date in New York. Earlier replay requires archived price vintages.")
    if sample.sample_dates[1] >= decision_date or len(sample.returns) != 60:
        raise ValueError("The snapshot must contain 60 aligned returns ending before the decision date.")
    end = sample.sample_dates[1]
    if decision_date.year * 12 + decision_date.month - (end.year * 12 + end.month) != 1:
        raise ValueError("The newest close must be in the latest completed month for the capture date.")
    gross = np.asarray(gross_returns, dtype=float)
    if gross.shape != (len(TICKERS),) or not np.all(np.isfinite(gross)) or np.any(gross <= -1) or np.any(gross > 1):
        raise ValueError("Enter one finite forward return per ETF, above −100% and at most 100%.")
    if not np.isfinite(cost) or not 0 <= cost <= 1:
        raise ValueError("Annual investor cost must be between 0% and 100%.")
    return tuple(fit_window(sample, mandate, gross, cost, months) for months in (36, 60))


def downside_returns(gross_returns, shock):
    """Apply a decimal percentage-point reduction to the credit and equity sleeves."""
    return tuple(value - shock if ticker in ("LQD", "VT") else value
                 for ticker, value in zip(TICKERS, gross_returns))


def evaluate_etf(weights, mandate, gross, cost, risk):
    weights = np.asarray(weights, dtype=float)
    _, expected, volatility = portfolio_metrics(weights, gross, risk, cost)
    failures = tuple(label for label, passed in (
        ("Modeled IG bond floor", BONDS @ weights + TOL >= mandate.min_bonds),
        ("Modeled reserve floor", RESERVE @ weights + TOL >= mandate.min_reserve),
        ("Expected net return target", expected + TOL >= mandate.target),
    ) if not passed)
    return ETFCase(tuple(float(w) for w in weights), expected, volatility, failures)


def modeled_floors(mandate):
    return (np.vstack((np.eye(len(TICKERS)), BONDS, RESERVE)),
            np.r_[np.zeros(len(TICKERS)), mandate.min_bonds, mandate.min_reserve])


def etf_frontier(mandate, gross, cost, risk, maximum, points=13):
    if maximum is None:
        return ()
    rows, bounds = modeled_floors(mandate)
    net = np.asarray(gross) - cost
    lowest = minimum_variance(rows, bounds, risk) @ net
    return tuple(
        (float(np.sqrt(weights @ risk @ weights)), float(weights @ net))
        for target in np.unique(np.linspace(min(lowest, maximum), maximum, points))
        for weights in (minimum_variance(np.vstack((rows, net)), np.r_[bounds, target], risk),)
    )


def fit_window(sample, mandate, gross, cost, months):
    risk = sample.returns.tail(months).cov().to_numpy() * 12
    if not np.isfinite(risk).all():
        raise ValueError(f"{months}-month covariance contains nonfinite inputs.")
    eigenvalues = np.linalg.eigvalsh(risk)
    if eigenvalues[0] <= 0 or eigenvalues[0] <= eigenvalues[-1] * 1e-10:
        raise ValueError(f"{months}-month covariance is singular or ill-conditioned. Review the panel and estimator.")

    # Fund roles are provisional. Issuer exemptions and five-day liquidity are unverified.
    rows, bounds = modeled_floors(mandate)
    net = gross - cost

    portfolios = {name: evaluate_etf(weights, mandate, gross, cost, risk) for name, weights in BASELINES}
    maximum = max((float(weights @ net) for weights in feasible_vertices(rows, bounds)), default=None)
    if maximum is None:
        decision = "Defer. Provisional bond and reserve floors have no feasible intersection."
    elif maximum + TOL < mandate.target:
        decision = "Defer. Expected net target exceeds the provisional modeled ceiling."
    else:
        weights = minimum_variance(np.vstack((rows, net)), np.r_[bounds, min(maximum, mandate.target)], risk)
        checked = evaluate_etf(weights, mandate, gross, cost, risk)
        if checked.modeled_failures:
            raise ArithmeticError("ETF candidate failed a modeled rule.")
        portfolios["Constrained candidate"] = checked
        decision = ("Due diligence only. Confirm ETF eligibility, issuer treatment, redemption evidence, "
                    "fund practices and loss tolerance before considering approval.")
    return WindowResult(months, sample.prices.index[-months - 1].date(), sample.sample_dates[1],
                        tuple(tuple(float(x) for x in row) for row in risk), maximum, portfolios, decision)
