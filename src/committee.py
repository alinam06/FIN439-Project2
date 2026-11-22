"""Student policy separating modeled feasibility, investment disposition, and process use."""

from dataclasses import dataclass
import numpy as np

from src.assumptions import ANNUAL_COST, ASSETS
from src.portfolio import BONDS, COMPANIES, GROSS_RETURNS, RESERVE, TOL, active_sets

ACTIONS = ("ADOPT", "ALLOCATE TO", "REBALANCE", "PILOT", "REJECT")
EXECUTION = ACTIONS[:3]


@dataclass(frozen=True)
class CommitteeDecision:
    action: str
    ask: str
    blocked: tuple[str, ...]
    triggers: tuple[str, ...]
    stops: tuple[str, ...]
    feasibility: str
    process: str = "Paper-test the evaluation process."
    live_fraction: float = 0.0


def recommendation(result, signal=None, requested="PILOT", *, illustrative=False):
    triggers = ("Review at annual rebalance and when the modeled return ceiling falls below target.",
                "Recheck the bond and reserve floors, issuer evidence and redemption terms after material changes.")
    if signal is None or signal.status == "Unavailable":
        triggers += ("Credit signal unavailable. Obtain dated evidence before relying on it.",)
    elif signal.status == "Review":
        triggers += ("Credit spread widening. Review credit and equity downside before changing an allocation.",)
    else:
        triggers += ("Credit spread: monitor alongside issuer, liquidity and downside evidence.",)
    candidate = result.portfolios[2] if len(result.portfolios) == 3 else None
    failures = tuple(rule.name for rule in candidate.rules if rule.status == "Fail") if candidate else ()
    unresolved = tuple(rule.name for rule in candidate.rules if rule.status == "Unverified") if candidate else ()
    stops = ("Stop on a hard mandate breach, an infeasible target, or invalid model inputs.",
             "Keep live deployment at 0% until eligibility, liquidity and client loss tolerance are resolved "
             "and the committee authorizes an action.")
    feasibility = ("No target-meeting candidate" if candidate is None else
                   "Active allocation fails modeled checks" if failures else "Modeled checks met")
    if candidate is None or failures:
        reason = "No feasible optimized candidate exists." if candidate is None else "Modeled failures: " + ", ".join(failures) + "."
        if illustrative:
            reason += " This is an illustrative result."
        return CommitteeDecision("REJECT", f"Defer deployment. {reason}", failures, triggers, stops, feasibility)
    if requested == "REJECT":
        return CommitteeDecision("REJECT", "Record the requested rejection and its rationale.",
                                 unresolved, triggers, stops, feasibility)
    hold = f" Defer {requested} pending review." if requested in EXECUTION else ""
    if illustrative:
        return CommitteeDecision("ILLUSTRATIVE ONLY", "The classroom allocation validates the method and carries no investment recommendation.",
                                 unresolved, triggers, stops, feasibility)
    return CommitteeDecision("HOLD", "Review robustness, investor suitability, and implementation evidence before seeking authorization."
                             + hold, unresolved, triggers, stops, feasibility)


def decision_for(context, signal=None, requested="PILOT", *, analysis=None):
    return recommendation(context.proposal if analysis is None else analysis, signal, requested,
                          illustrative=context.sample is None)


def weight_ranges(mandate):
    """Independent weight extrema for the classroom feasible set, including its return floor."""
    net = GROSS_RETURNS - ANNUAL_COST
    rows = np.vstack((np.eye(len(ASSETS)), BONDS, RESERVE, *(-mask for mask in COMPANIES.values()), net))
    bounds = np.r_[np.zeros(len(ASSETS)), mandate.min_bonds, mandate.min_reserve,
                   [-mandate.max_company] * len(COMPANIES), mandate.target]
    vertices = []
    for matrix, rhs in active_sets(rows, bounds, len(ASSETS) - 1):
        weights = np.linalg.solve(matrix, rhs)
        if np.all(rows @ weights >= bounds - TOL):
            vertices.append(weights)
    if not vertices:
        return ()
    return tuple(zip(np.clip(np.min(vertices, axis=0), 0, 1), np.clip(np.max(vertices, axis=0), 0, 1)))
