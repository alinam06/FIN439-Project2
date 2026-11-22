"""Committee findings derived from the active investment model."""

from dataclasses import dataclass

import numpy as np

from src.committee import decision_for
from src.historical import TICKERS
from src.judgment import attribution, resilience, restrictions, transition
from src.portfolio import TOL


@dataclass(frozen=True)
class Finding:
    question: str
    evidence: str
    implication: str
    action: str
    reversal: str


@dataclass(frozen=True)
class Briefing:
    action: str
    ask: str
    capital: float
    findings: tuple[Finding, ...]
    approval_gap: str
    risk_driver: str
    register: tuple[tuple[str, str], ...]
    feasibility: str
    process: str


ETF_UNIVERSE = ", ".join(TICKERS)
DATED_CREDIT_EVIDENCE = ("Dated FRED evidence (November 21, 2026): +12 bp over 20 eligible observations. "
                         "It prompted credit and equity downside review on that decision date.")


def model_scope(context):
    if context.sample is None:
        return (f"Classroom demonstration · Validates the construction process with illustrative sleeves. "
                f"The Project 2 investment universe is {ETF_UNIVERSE}. Classroom sleeves are non-investable examples.")
    return (f"Reviewed ETF snapshot · Evaluates the actual Project 2 universe: {ETF_UNIVERSE}. "
            "Expected returns are explicit assumptions. Historical data estimate risk.")


def project_etf_finding(reviewed_context=None):
    if reviewed_context is None:
        return ("**Previously documented ETF finding:** BIL, IEF, LQD and VT had a 6.65% modeled net ceiling "
                "versus the 7.00% Lab 13 objective, so the documented allocation decision was REJECT, with $0 live. "
                "The authorized snapshot is unavailable here. This session has not reproduced that analysis.")
    maximum = reviewed_context.analysis.max_net_return
    target = reviewed_context.mandate.target
    decision = decision_for(reviewed_context)
    if maximum is None:
        return f"**Reviewed Project 2 universe · {decision.action}:** No feasible modeled allocation. $0 live."
    return (f"**Reviewed Project 2 universe · {decision.action}:** BIL, IEF, LQD and VT have a {maximum:.2%} "
            f"modeled net ceiling versus the original {target:.2%} objective ({(maximum-target)*10000:+.0f} bp). "
            "$0 live. Calculated from the authorized local snapshot.")


def investment_brief(context, signal=None, requested="PILOT"):
    policy = decision_for(context, signal, requested)
    mandate, active = context.mandate, context.active
    maximum = context.analysis.max_net_return
    modeled = resilience(context)
    findings = []
    if maximum is None:
        findings.append(Finding("Feasibility", "Modeled limits have no feasible weight intersection.",
                                "A return estimate cannot restore inconsistent allocation limits.",
                                "Defer the proposal.", "Reconcile the modeled restrictions with the client."))
    else:
        gap = maximum - mandate.target
        evidence = f"The maximum is {maximum:.2%} vs {mandate.target:.2%} required ({gap*10000:+.1f} bp)."
        implication = ("Even the highest-return permissible modeled mix misses the objective." if gap < -TOL else
                       "The ceiling is the best case across modeled weights under the fixed return assumptions.")
        if active:
            held = active.net_return - mandate.target
            evidence += f" Held margin {held*10000:+.1f} bp."
            if abs(held) <= TOL:
                implication = "The selected weights meet the objective at the modeled boundary."
        findings.append(Finding("Can the portfolio meet the target?", evidence, implication,
                                "Withhold deployment." if policy.action == "REJECT" else "Test assumption sensitivity.",
                                f"Ceiling below {mandate.target:.2%} stops the proposal."))
    risk_driver = "Unavailable without active weights"
    if active:
        stats = attribution(active.weights, context.gross_returns, context.risk, context.annual_cost)
        if stats.risk_by_asset is not None:
            i = int(np.argmax(stats.risk_by_asset))
            risk_driver = context.asset_names[i]
            share = stats.risk_by_asset[i] / stats.volatility
            benchmark = context.analysis.portfolios[1]
            findings.append(Finding("Where is the risk concentrated?",
                                    f"{risk_driver}: {active.weights[i]:.1%} of capital and {share:.1%} of modeled volatility.",
                                    f"The active mix changes volatility by {(active.volatility-benchmark.volatility)*100:+.2f} pp versus the benchmark.",
                                    "Review downside in the largest risk sleeve.",
                                    "Set and test the client’s acceptable loss before live approval."))
    failed = tuple(rule.name for rule in active.rules if rule.status == "Fail") if active else ()
    pending = tuple(rule.name for rule in active.rules if rule.status == "Unverified") if active else ()
    gaps = []
    if any("loss tolerance" in rule.lower() for rule in pending):
        gaps.append("Client annual loss tolerance is undefined.")
    if any("rede" in rule.lower() for rule in pending):
        gaps.append("Five-day redemption needs evidence.")
    if any("issuer" in rule.lower() or "eligibility" in rule.lower() for rule in pending):
        gaps.append("Instrument eligibility needs evidence.")
    gap_text = (" ".join(gaps) if active else
                "No candidate under the active inputs. Resolve feasibility before evaluating implementation.")
    if active and not gap_text:
        gap_text = "Explicit committee authorization is required."
    if failed:
        findings.insert(0, Finding("Which checks fail?", ", ".join(failed) + ".",
                                  "The active weights do not meet all modeled tests.",
                                  "Reject these weights.", "Recompute a candidate that clears the failed checks."))
        gap_text = "Resolve the failed modeled checks first. " + gap_text
    elif pending:
        findings.append(Finding("Can the committee deploy?", gap_text,
                                "Modeled annual volatility does not establish a maximum loss.",
                                "Set loss tolerance and assign evidence owners.",
                                "Verify eligibility and redemption, then obtain explicit approval."))
    register = (("Process", policy.process),
                ("Withhold", "All live capital. A separate committee vote is required."),
                ("Verify", gap_text),
                ("Investigate", findings[0].reversal if not active or failed else
                 f"Stress {risk_driver} and recheck the {modeled.feasible_cost_break_even*10000:.1f} bp modeled cost boundary."
                 if modeled.feasible_cost_break_even is not None and modeled.feasible_cost_break_even >= 0
                 else "Recheck the feasible return set before approving any deployment."))
    return Briefing(policy.action, policy.ask, mandate.portfolio_value * policy.live_fraction, tuple(findings[:3]),
                    gap_text, risk_driver, register, policy.feasibility, policy.process)


def monitoring_rows(context, signal=None):
    mandate, active = context.mandate, context.active
    evidence = resilience(context)
    rate = lambda x: "Unavailable" if x is None else f"{x:.2%}"
    bp = lambda x: "Unavailable" if x is None else f"{x*10000:.1f} bp"
    ceiling = context.analysis.max_net_return
    target_status = ("No feasible modeled set" if ceiling is None else
                     "Meets objective" if ceiling >= mandate.target - TOL else "Below objective")
    rows = [("Objective", "Feasible net return", f"{rate(ceiling)} · {target_status}", f"At least {mandate.target:.2%}",
             "No target-meeting mix below the floor.", "Stop and review the modeled opportunity set.")]
    for check in restrictions(context):
        if not check.objective:
            condition = "At most" if check.name.endswith(" cap") else "At least"
            rows.append(("Hard modeled limit", check.name, f"{rate(check.exposure)} · {check.status}",
                         f"{condition} {rate(check.limit)}", "A breach fails the modeled mandate.",
                         "Reject weights that breach the limit."))
    if active is None:
        for name, bound in (("Investment-grade bond floor", mandate.min_bonds),
                            ("Liquid reserve floor", mandate.min_reserve)):
            rows.append(("Hard modeled limit", name, "No candidate to assess", f"At least {bound:.2%}",
                         "A breach fails the modeled mandate.", "Reject weights that breach the limit."))
    if context.sample is not None or active is None:
        rows.append(("Hard evidence gate", "Nonexempt company exposure", "Unverified" if active else "No candidate to assess",
                     f"At most {mandate.max_company:.2%}", "An excess exposure fails the mandate.",
                     "Verify look-through and reject any breach."))
    rows.extend([
        ("Hard evidence gate", "Five-day redemption", "Unverified" if mandate.min_five_day else "No minimum",
         f"At least {mandate.min_five_day:.2%} if required", "Missing evidence or a verified shortfall blocks approval.",
         "Withhold deployment until verified."),
        ("Analytical indicator", "Recurring annual costs", bp(context.annual_cost),
         (f"Held ceiling {bp(evidence.held_cost_break_even)} · modeled set {bp(evidence.feasible_cost_break_even)}"
          if evidence.feasible_cost_break_even is None or evidence.feasible_cost_break_even >= -TOL
          else "No nonnegative recurring cost reaches target"),
         "Higher cost erodes net return.", "Reprice before trading. Stop if no mix reaches target."),
        ("Analytical indicator", "Parallel equity forecast cut", "0 bp in base assumptions",
         (f"Held {bp(evidence.held_equity_cut)} · modeled set {bp(evidence.feasible_equity_cut)}"
          if not evidence.equity_independent else "A mix with no equity exposure can meet the target"),
         "A cut beyond the boundary removes feasibility. A negative cut means an uplift is needed.", "A negative cut means an uplift is needed. Refresh forecasts and rerun feasibility."),
        ("Investor preference", "Annual loss limit", "Unknown", "Client must specify",
         "Suitability remains unresolved.", "Withhold live authorization and ask the client."),
        ("Monitoring input", "BAA10Y",
         (f"{signal.status} · {signal.change_pp*100:+.1f} bp" if signal and signal.change_pp is not None
          else signal.status if signal else "Unavailable"),
         "Positive change across 20 eligible observations",
         "Widening prompts a credit and equity review.", "Review downside. Keep weights fixed."),
    ])
    return rows


def scenario_row(label, assumption, context, analysis, held, rate, signal, requested, *, reference=False, target=None):
    candidate = analysis.portfolios[2] if len(analysis.portfolios) == 3 else None
    active = context.active
    trade = None if reference else transition(active, candidate, context.mandate.portfolio_value, rate)
    if reference:
        effect = f"Reference · {active.verdict}" if active else "Reference · no feasible proposal"
    elif candidate is None:
        effect = "No feasible mix under stress"
    elif held is None:
        effect = "Stressed candidate only"
    elif held.verdict == "Fail":
        failures = [rule.name for rule in held.rules if rule.status == "Fail"]
        effect = "Held fails: " + ", ".join(failures) + ". Reoptimization restores modeled feasibility."
    elif active and held.volatility > active.volatility + TOL:
        effect = "Held passes modeled checks with higher risk. Suitability remains unverified."
    else:
        effect = "Modeled feasibility retained. Suitability remains unverified."
    pct = lambda x: "Unavailable" if x is None else f"{x:.2%}"
    return {
        "_ceiling": analysis.max_net_return, "Scenario": label, "Committee action": decision_for(context, signal, requested, analysis=analysis).action,
        "Investment effect": effect, "Changed assumption": assumption,
        "Net target": pct(context.mandate.target if target is None else target),
        "Held net return": pct(held.net_return if held else None),
        "Reoptimized net return": "—" if reference else pct(candidate.net_return if candidate else None),
        "Modeled maximum": pct(analysis.max_net_return),
        "Held volatility": pct(held.volatility if held else None),
        "Reoptimized volatility": "—" if reference else pct(candidate.volatility if candidate else None),
        "Largest move": (f"{context.asset_names[trade.largest_index]} "
                         f"{abs(trade.changes[trade.largest_index])*100:.2f} pp" if trade else "—"),
        "Transition cost": f"${trade.expense:,.2f}" if trade and trade.expense is not None else "—",
    }


def exclusion_effect(context, index):
    """Remove the sleeve and redistribute proportionally. This is not an optimized trade."""
    active = context.active
    if active is None:
        return None
    weight = active.weights[index]
    if weight <= TOL or weight >= 1 - TOL:
        return None
    weights = [0 if i == index else w / (1 - weight) for i, w in enumerate(active.weights)]
    return context.evaluate(weights, "Pro rata exclusion")


def stress_finding(original, base_ceiling, base_target, challenge, policy):
    """Summarize the scenario without turning a numerical change into a policy threshold."""
    analysis, held = challenge.analysis, challenge.held
    candidate = analysis.portfolios[2] if len(analysis.portfolios) == 3 else None
    ceiling = analysis.max_net_return
    if challenge.label == "Base case":
        values = (f"Active mix: {original.net_return:.2%} net and {original.volatility:.2%} volatility. "
                  if original else "")
        return f"Reference only. {values}Use this case to compare shocks."

    changes = []
    if ceiling is not None:
        change = f" ({(ceiling-base_ceiling)*10000:+.1f} bp)" if base_ceiling is not None else ""
        changes.append(f"Ceiling {ceiling:.2%}{change} versus {challenge.target:.2%} target.")
    if original and held:
        changes.append(f"Held net {held.net_return:.2%} ({(held.net_return-original.net_return)*10000:+.1f} bp), "
                       f"volatility {held.volatility:.2%} ({(held.volatility-original.volatility)*100:+.2f} pp).")

    label = f"**{policy.action}** after reoptimization."
    same_ceiling = ceiling is not None and base_ceiling is not None and abs(ceiling - base_ceiling) <= TOL
    same_target = abs(challenge.target - base_target) <= TOL
    if candidate is None:
        reason = ("Modeled limits leave no feasible weights." if ceiling is None else
                  "No modeled allocation meets the stressed target." if ceiling < challenge.target - TOL
                  else "No successor was produced.")
        action = ("This shock leaves the feasibility finding unchanged. Continue withholding capital."
                  if same_ceiling and same_target else "Stop the proposal and review the challenged inputs.")
        return f"{reason} {' '.join(changes)} {label} {action}"
    if held and held.verdict == "Fail":
        failures = ", ".join(rule.name for rule in held.rules if rule.status == "Fail")
        return (f"Held weights fail: {failures}. {' '.join(changes)} The successor reaches "
                f"{candidate.net_return:.2%} net at {candidate.volatility:.2%} volatility. {label} "
                "Set aside the held weights. Compare the successor’s risk and implementation costs before reconsidering.")
    if (original and held and same_ceiling and same_target and abs(held.net_return - original.net_return) <= TOL
            and abs(held.volatility - original.volatility) <= TOL):
        return (f"No change in modeled held return or volatility. {' '.join(changes)} {label} "
                "This shock provides little new evidence for the decision. Keep authorization unchanged.")
    if original and held and same_ceiling and same_target and abs(held.net_return - original.net_return) <= TOL:
        risk_change = held.volatility - original.volatility
        relative = f" ({risk_change / original.volatility:+.1%} relative to starting risk)" if original.volatility else ""
        return (f"Held return and feasibility are unchanged. {' '.join(changes)} {label} "
                f"The volatility move{relative} has little effect on this authorization decision. "
                "Keep authorization unchanged.")
    return (f"The stressed solver produced a modeled candidate. {' '.join(changes)} {label} "
            "Use the comparison for review. Investor suitability and implementation still require evidence.")
