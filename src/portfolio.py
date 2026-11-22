"""Deterministic allocation, optimization and mandate checks."""

from dataclasses import dataclass
from itertools import combinations
import math

import numpy as np

from src.assumptions import ANNUAL_COST, ASSETS, CORRELATIONS

TOL = 1e-9


@dataclass(frozen=True)
class Mandate:
    portfolio_value: float = 5_000_000.0
    horizon: int = 15
    target: float = .07
    min_bonds: float = .25
    min_reserve: float = .10
    max_company: float = .08
    min_five_day: float = .90

    def __post_init__(self):
        if not math.isfinite(self.portfolio_value) or self.portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive and finite.")
        if type(self.horizon) is not int or not 1 <= self.horizon <= 100:
            raise ValueError("Horizon must be a whole number from 1 to 100 years.")
        if not math.isfinite(self.target) or not -1 < self.target <= 1:
            raise ValueError("Target must be above −100% and at most 100%.")
        if not all(0 <= value <= 1 for value in (
            self.min_bonds, self.min_reserve, self.max_company, self.min_five_day
        )):
            raise ValueError("Allocation limits must be between 0% and 100%.")

    @property
    def target_value(self):
        value = self.portfolio_value * (1 + self.target) ** self.horizon
        if not math.isfinite(value):
            raise ValueError("Target ending value exceeds the supported numeric range.")
        return value


@dataclass(frozen=True)
class Rule:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class Portfolio:
    name: str
    weights: tuple[float, ...]
    net_return: float
    volatility: float
    rules: tuple[Rule, ...]

    @property
    def verdict(self):
        statuses = {rule.status for rule in self.rules}
        if "Fail" in statuses:
            return "Fail"
        if "Unverified" in statuses:
            return "Unverified"
        return "Pass"


@dataclass(frozen=True)
class Analysis:
    portfolios: tuple[Portfolio, ...]
    max_net_return: float | None
    decision: str
    frontier: tuple[tuple[float, float], ...]


def covariance(volatility, correlation):
    volatility = np.asarray(volatility, dtype=float)
    correlation = np.asarray(correlation, dtype=float)
    if (volatility.ndim != 1 or not volatility.size
        or correlation.shape != (volatility.size, volatility.size)
        or not np.all(np.isfinite(volatility)) or np.any(volatility <= 0)
        or not np.all(np.isfinite(correlation)) or np.any(np.abs(correlation) > 1)
        or not np.allclose(correlation, correlation.T, atol=TOL, rtol=0)
        or not np.allclose(np.diag(correlation), 1, atol=TOL, rtol=0)):
        raise ValueError("Risk inputs require positive volatilities and symmetric correlations in [-1, 1] with unit diagonal.")
    correlation = (correlation + correlation.T) / 2
    if np.linalg.eigvalsh(correlation)[0] < -TOL:
        raise ValueError("The correlation matrix must be positive semidefinite.")
    return np.outer(volatility, volatility) * correlation


GROSS_RETURNS = np.array([asset.gross_return for asset in ASSETS])
BONDS = np.array([asset.investment_grade for asset in ASSETS], dtype=float)
RESERVE = np.array([asset.reserve_eligible for asset in ASSETS], dtype=float)
COMPANIES = {
    company: np.array([asset.company == company for asset in ASSETS], dtype=float)
    for company in sorted({asset.company for asset in ASSETS if asset.company is not None})
}


def portfolio_metrics(weights, gross_returns, risk, annual_cost=0.0):
    """Return gross return, net return and volatility for valid long-only weights.

    Supply annual expected returns and a covariance matrix from covariance().
    """
    weights = np.asarray(weights, dtype=float)
    gross_returns = np.asarray(gross_returns, dtype=float)
    risk = np.asarray(risk, dtype=float)
    if (gross_returns.ndim != 1 or not gross_returns.size
        or weights.shape != gross_returns.shape or not np.all(np.isfinite(weights))):
        raise ValueError("Provide one finite weight per asset.")
    if np.min(weights) < -TOL or abs(weights.sum() - 1) > TOL:
        raise ValueError("Long-only weights must be nonnegative and sum to 100%.")
    if (not np.all(np.isfinite(gross_returns)) or not math.isfinite(annual_cost) or annual_cost < 0
        or risk.shape != (weights.size, weights.size) or not np.all(np.isfinite(risk))):
        raise ValueError("Supply finite annual returns, covariance and a nonnegative cost.")
    gross_return = float(weights @ gross_returns)
    variance = float(weights @ risk @ weights)
    if variance < -TOL * np.max(np.abs(risk)):
        raise ValueError("The supplied covariance implies negative portfolio variance.")
    return gross_return, gross_return - annual_cost, math.sqrt(max(0, variance))


def evaluate(name, weights, mandate, risk, *, gross_returns=GROSS_RETURNS, annual_cost=ANNUAL_COST):
    weights = np.asarray(weights, dtype=float)
    _, net_return, volatility = portfolio_metrics(weights, gross_returns, risk, annual_cost)
    bonds = BONDS @ weights
    reserve = RESERVE @ weights
    largest_company = max((mask @ weights for mask in COMPANIES.values()), default=0.0)

    def check(label, condition, detail):
        return Rule(label, "Pass" if condition else "Fail", detail)

    rules = (
        check("Fully invested", abs(weights.sum() - 1) <= TOL, f"Total weight {weights.sum():.2%}."),
        check("Long-only / no borrowing / no shorting",
              np.min(weights) >= -TOL and np.abs(weights).sum() <= 1 + TOL,
              "Checks modeled position weights and gross exposure."),
        Rule("No derivatives", "Unverified",
             "The sample uses unlevered cash securities and fund sleeves. Verify actual fund holdings and policies."),
        Rule("Underlying fund leverage", "Unverified", "Verify leverage policies and exposures for actual funds."),
        check("Investment-grade bonds", bonds + TOL >= mandate.min_bonds,
              f"Model allocation {bonds:.2%} against a {mandate.min_bonds:.2%} minimum."),
        check("Cash or liquid government reserve", reserve + TOL >= mandate.min_reserve,
              f"Model allocation {reserve:.2%} against a {mandate.min_reserve:.2%} minimum."),
        check("Company concentration (model)", largest_company <= mandate.max_company + TOL,
              f"Largest modeled nonexempt issuer {largest_company:.2%} against a {mandate.max_company:.2%} cap."),
        Rule("Issuer evidence", "Unverified",
             "Confirm actual legal issuers and fund exemptions before implementation."),
        Rule("Redeemable within five business days",
             "Pass" if mandate.min_five_day == 0 else "Unverified",
             f"Required share {mandate.min_five_day:.2%}. The sample contains no validated redemption terms."),
        check("Expected net return objective", net_return + TOL >= mandate.target,
              f"Modeled {net_return:.2%} against a {mandate.target:.2%} annual target."),
        Rule("Annual rebalancing", "Unverified",
             "Annual schedule specified. A static allocation provides no execution history."),
        Rule("Annual loss tolerance", "Unverified", "The client has yet to specify an annual loss limit."),
    )
    return Portfolio(name, tuple(float(w) for w in weights), net_return, volatility, rules)


def active_sets(rows, bounds, size):
    """Enumerate independent active inequality sets on the fully invested simplex."""
    for active in combinations(range(len(rows)), size):
        indices = list(active)
        matrix = np.vstack((np.ones(rows.shape[1]), rows[indices]))
        if np.linalg.matrix_rank(matrix) == len(matrix):
            yield matrix, np.r_[1.0, bounds[indices]]


def minimum_variance(rows, bounds, risk):
    """Find the best feasible face minimum of a small strictly convex quadratic."""
    best = None
    best_variance = math.inf
    try:
        factor = np.linalg.cholesky(risk)
    except np.linalg.LinAlgError as error:
        raise ValueError("Optimization requires a positive-definite covariance matrix.") from error
    for size in range(rows.shape[1]):
        for matrix, rhs in active_sets(rows, bounds, size):
            # With C = L Lᵀ and z = Lᵀw, minimize ||z|| subject to A L⁻ᵀ z = b.
            scaled = np.linalg.solve(factor, matrix.T).T
            z = np.linalg.lstsq(scaled, rhs, rcond=None)[0]
            weights = np.linalg.solve(factor.T, z)
            if (np.max(np.abs(matrix @ weights - rhs)) <= TOL
                and np.all(rows @ weights >= bounds - TOL)):
                variance = weights @ risk @ weights
                if variance < best_variance:
                    best, best_variance = weights, variance
    if best is None:
        raise ArithmeticError("No verified solution returned for a feasible model. Review the scenario inputs.")
    return np.where(np.abs(best) <= 32 * np.finfo(float).eps, 0.0, best)


def classroom_floors(mandate):
    rows = np.vstack((np.eye(len(ASSETS)), BONDS, RESERVE, *(-mask for mask in COMPANIES.values())))
    bounds = np.r_[np.zeros(len(ASSETS)), mandate.min_bonds, mandate.min_reserve,
                   [-mandate.max_company] * len(COMPANIES)]
    return rows, bounds


def feasible_vertices(rows, bounds):
    for matrix, rhs in active_sets(rows, bounds, rows.shape[1] - 1):
        weights = np.linalg.solve(matrix, rhs)
        if np.all(rows @ weights >= bounds - TOL):
            yield weights


def analyze(mandate, frontier_points=13, *, gross_returns=GROSS_RETURNS,
            volatilities=tuple(asset.volatility for asset in ASSETS),
            correlations=CORRELATIONS, annual_cost=ANNUAL_COST):
    risk = covariance(volatilities, correlations)
    gross_returns = np.asarray(gross_returns, dtype=float)
    if gross_returns.shape != GROSS_RETURNS.shape or risk.shape != (len(ASSETS), len(ASSETS)):
        raise ValueError("Provide risk and return inputs for every classroom asset.")
    net_returns = gross_returns - annual_cost

    def assessed(name, weights):
        return evaluate(name, weights, mandate, risk, gross_returns=gross_returns, annual_cost=annual_cost)
    equal = np.full(len(ASSETS), 1 / len(ASSETS))
    benchmark = np.array([0, 0, .40, .60, 0])
    portfolios = (
        assessed("Equal weight", equal),
        assessed("60/40 global equity / IG bonds", benchmark),
    )
    rows, bounds = classroom_floors(mandate)
    vertex_returns = [float(weights @ net_returns) for weights in feasible_vertices(rows, bounds)]

    if not vertex_returns:
        return Analysis(portfolios, None,
                        "Defer. The modeled allocation constraints have no feasible intersection.", ())
    maximum = max(vertex_returns)

    def at_target(target):
        return minimum_variance(np.vstack((rows, net_returns)), np.r_[bounds, target], risk)

    if mandate.target > maximum + TOL:
        decision = ("Defer. The net return target exceeds the maximum under the modeled constraints. "
                    "Review the objective and assumptions with the client.")
    else:
        weights = at_target(min(mandate.target, maximum))
        optimized = assessed("Constrained minimum volatility", weights)
        if any(rule.status == "Fail" for rule in optimized.rules):
            raise ArithmeticError("Optimized weights failed a modeled mandate check.")
        portfolios += (optimized,)
        redemption = " verify five-day redemption," if mandate.min_five_day > 0 else ""
        decision = ("Advance the optimized mix to due diligence. Confirm issuers, fund exemptions, "
                    "bond and reserve eligibility, fund leverage and derivatives policies,"
                    f"{redemption} and clarify annual loss tolerance before seeking allocation approval.")

    frontier = []
    if frontier_points:
        min_risk = minimum_variance(rows, bounds, risk)
        lowest = float(min_risk @ net_returns)
        targets = np.unique(np.linspace(min(lowest, maximum), maximum, frontier_points))
        for target in targets:
            weights = at_target(target)
            frontier.append((float(np.sqrt(weights @ risk @ weights)), float(weights @ net_returns)))
    return Analysis(portfolios, maximum, decision, tuple(frontier))
