"""Calculated evidence for a paper allocation decision."""

from dataclasses import dataclass, replace

import numpy as np

from src.committee import decision_for
from src.etf_portfolio import modeled_floors
from src.portfolio import COMPANIES, TOL, Analysis, Portfolio, classroom_floors, feasible_vertices, portfolio_metrics


@dataclass(frozen=True)
class Attribution:
    gross_by_asset: tuple[float, ...]
    risk_by_asset: tuple[float, ...] | None
    annual_cost: float
    gross_return: float
    net_return: float
    volatility: float


def attribution(weights, gross_returns, risk, annual_cost):
    gross, net, volatility = portfolio_metrics(weights, gross_returns, risk, annual_cost)
    weights = np.asarray(weights, dtype=float)
    risk = np.asarray(risk, dtype=float)
    risk_by_asset = None if volatility == 0 else tuple(weights * (risk @ weights) / volatility)
    return Attribution(tuple(weights * gross_returns), risk_by_asset, annual_cost, gross, net, volatility)


@dataclass(frozen=True)
class StressChallenge:
    label: str
    analysis: Analysis
    held: Portfolio | None
    target: float
    trade_rate: float | None


@dataclass(frozen=True)
class Transition:
    changes: tuple[float, ...]
    largest_index: int
    gross_share: float
    one_way_share: float
    gross_dollars: float
    one_way_dollars: float
    expense: float | None


def transition(original, candidate, portfolio_value, trade_rate):
    if original is None or candidate is None:
        return None
    changes = tuple(new - old for new, old in zip(candidate.weights, original.weights, strict=True))
    absolute = tuple(abs(delta) for delta in changes)
    gross_share = sum(absolute)
    gross_dollars = gross_share * portfolio_value
    return Transition(changes, int(np.argmax(absolute)), gross_share, gross_share / 2,
                      gross_dollars, gross_dollars / 2, None if trade_rate is None else gross_dollars * trade_rate)


def margin(value, target):
    return None if value is None else value - target


@dataclass(frozen=True)
class Resilience:
    held_margin: float | None
    ceiling_margin: float | None
    held_cost_break_even: float | None
    feasible_cost_break_even: float | None
    held_equity_cut: float | None
    feasible_equity_cut: float | None
    equity_independent: bool


def resilience(context):
    held = context.active
    target = context.mandate.target
    held_margin = margin(held.net_return if held else None, target)
    ceiling_margin = margin(context.analysis.max_net_return, target)
    equity_mask = np.array([name in ("Global equity index fund", "Fictional company stock", "VT")
                            for name in context.asset_names], dtype=float)
    equity_weight = float(equity_mask @ held.weights) if held else 0
    modeled_floors_for = classroom_floors if context.sample is None else modeled_floors
    net_returns = np.asarray(context.gross_returns) - context.annual_cost
    cuts = []
    equity_independent = False
    for vertex in feasible_vertices(*modeled_floors_for(context.mandate)):
        exposure = float(vertex @ equity_mask)
        headroom = float(vertex @ net_returns) - target
        if exposure > TOL:
            cuts.append(headroom / exposure)
        elif headroom >= -TOL:
            equity_independent = True
    return Resilience(
        held_margin, ceiling_margin,
        None if held_margin is None else context.annual_cost + held_margin,
        None if ceiling_margin is None else context.annual_cost + ceiling_margin,
        None if equity_weight <= TOL else held_margin / equity_weight,
        max(cuts) if cuts and not equity_independent else None, equity_independent,
    )


def reserve_sensitivity(context):
    """Test an explicitly hypothetical one-point increase in the reserve floor."""
    mandate = context.mandate
    tighter = min(1.0, mandate.min_reserve + .01)
    if tighter == mandate.min_reserve:
        return tighter, None
    floors = classroom_floors if context.sample is None else modeled_floors
    rows, bounds = floors(replace(mandate, min_reserve=tighter))
    net = np.asarray(context.gross_returns) - context.annual_cost
    return tighter, max((float(w @ net) for w in feasible_vertices(rows, bounds)), default=None)


@dataclass(frozen=True)
class Restriction:
    name: str
    exposure: float
    limit: float
    slack: float
    objective: bool = False

    @property
    def status(self):
        if self.slack < -TOL:
            return "Failed"
        return "At limit" if self.slack <= TOL else "Slack"


def restrictions(context):
    active = context.active
    if active is None:
        return ()
    mandate = context.mandate
    bonds, reserve = context.exposure(active.weights)
    checks = [
        Restriction("Investment-grade bond floor", bonds, mandate.min_bonds, bonds - mandate.min_bonds),
        Restriction("Liquid reserve floor", reserve, mandate.min_reserve, reserve - mandate.min_reserve),
        Restriction("Net return objective", active.net_return, mandate.target, active.net_return - mandate.target, True),
    ]
    if context.sample is None:
        for name, mask in COMPANIES.items():
            exposure = float(mask @ active.weights)
            checks.append(Restriction(f"{name} cap", exposure, mandate.max_company, mandate.max_company - exposure))
    return tuple(checks)


def signal_admission(signal, *, source_rejected=False):
    if source_rejected:
        return "Reject", "Source validation failed. Keep it out of the decision."
    if signal is None:
        return "Quarantine", "No reviewed archive is loaded. The separate dated FRED example is evidence only for its documented date."
    if signal.status == "Unavailable":
        return "Quarantine", signal.explanation
    return "Admit for monitoring", ("Eligible date-level observations pass the availability and freshness checks. "
                                    "Uploader provenance still needs review. The broad spread is a credit and "
                                    "equity risk indicator. It does not establish ETF-specific spreads or a trading rule.")


def driver_summary(context, result):
    i = int(np.argmax(result.gross_by_asset))
    return_driver = (f"{context.asset_names[i]} makes the largest contribution to gross expected return "
                     f"({result.gross_by_asset[i]:.2%} of portfolio value per year).")
    if result.risk_by_asset is None:
        return return_driver + " Volatility contribution is undefined at zero modeled volatility."
    j = int(np.argmax(result.risk_by_asset))
    risk_share = result.risk_by_asset[j] / result.volatility
    weight = context.active.weights[j]
    comparison = "above" if risk_share > weight + TOL else "below" if risk_share < weight - TOL else "equal to"
    return (f"{return_driver} {context.asset_names[j]} accounts for {risk_share:.1%} of modeled volatility, "
            f"{comparison} its {weight:.1%} capital weight. A holding count alone cannot establish risk diversification.")


@dataclass(frozen=True)
class CommitteePanel:
    action: str
    strategist: str
    risk_manager: str
    implementation: str
    synthesis: str


def committee_panel(context, signal, requested, challenge=None, *, source_rejected=False):
    policy = decision_for(context, signal, requested)
    active = context.active
    bounds = resilience(context)
    benchmarks = " and ".join(f"{p.name} {p.net_return:.2%} net ({p.verdict})"
                              for p in context.analysis.portfolios[:2])
    if bounds.ceiling_margin is None:
        finding = "The modeled limits have no feasible intersection."
    else:
        finding = f"Best modeled return is {(bounds.ceiling_margin + context.mandate.target):.2%} net ({bounds.ceiling_margin * 10000:+.1f} bp versus target)."
    strategist = f"{finding} References: {benchmarks}. Failed baselines still show what a simpler mix delivers."
    if active:
        comparison = context.analysis.portfolios[1]
        strategist += (f" Versus the benchmark, the active mix changes expected net return by "
                       f"{(active.net_return - comparison.net_return)*100:+.2f} pp and modeled volatility "
                       f"by {(active.volatility - comparison.volatility)*100:+.2f} pp.")
    risk_manager = "No active weights available for a risk judgment."
    if active:
        result = attribution(active.weights, context.gross_returns, context.risk, context.annual_cost)
        risk_manager = f"Annual modeled volatility is {result.volatility:.2%}. " + driver_summary(context, result)
        if challenge:
            candidate = challenge.analysis.portfolios[2] if len(challenge.analysis.portfolios) == 3 else None
            trade = transition(active, candidate, context.mandate.portfolio_value, challenge.trade_rate)
            if trade is None:
                risk_manager += f" {challenge.label}: {challenge.analysis.decision}"
            else:
                risk_manager += (f" {challenge.label}: {trade.one_way_share:.2%} one-way turnover "
                                 f"if reoptimized.")
    if context.windows:
        reference = active or context.analysis.portfolios[1]
        rates = [portfolio_metrics(reference.weights, context.gross_returns, window.annual_covariance,
                                   context.annual_cost)[2] for window in context.windows]
        name = "Active weights" if active else "Benchmark weights"
        risk_manager += f" {name}: {rates[0]:.2%} risk at 36 months and {rates[1]:.2%} at 60 months."
    else:
        risk_manager += " Historical ETF windows do not estimate this classroom allocation."
    risk_manager += " The client's annual loss tolerance remains unresolved."
    costs = context.annual_cost * context.mandate.portfolio_value
    pending = [r.name for r in active.rules if r.status == "Unverified"] if active else []
    implementation = (f"Recurring modeled cost is {context.annual_cost:.2%} (${costs:,.0f}/year). "
                      "Live allocation stays at 0%.")
    if pending:
        if any("redeem" in name.lower() or "redemption" in name.lower() for name in pending):
            implementation += " Obtain instrument-level redemption terms and confirm the modeled five-day minimum."
        if any("issuer" in name.lower() or "eligibility" in name.lower() for name in pending):
            implementation += " Obtain current holdings and instrument policies to verify issuer and eligibility treatment."
    implementation += " " + signal_admission(signal, source_rejected=source_rejected)[0] + " is the current disposition of the credit input."
    synthesis = policy.ask + " " + policy.process
    return CommitteePanel(policy.action, strategist, risk_manager, implementation, synthesis)
