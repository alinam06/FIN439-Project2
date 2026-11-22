"""Deterministic interpretation of the active investment decision."""

import re

from src.briefing import investment_brief, monitoring_rows
from src.committee import decision_for
from src.investment_context import ETF
from src.investment_views import adverse_summary, binding_checks
from src.judgment import attribution, driver_summary, resilience, signal_admission, transition
from src.portfolio import TOL, portfolio_metrics

SUGGESTIONS = (
    "Why this decision?",
    "Portfolio weights?",
    "Net return target?",
    "Biggest risks?",
    "Which constraints?",
    "Stress result?",
)


def suggested_questions(context):
    if context.optimized is None:
        return (SUGGESTIONS[0], "Return ceiling?", "Stress result?", "What would change approval?", "Credit signal?")
    if context.model == ETF:
        return (SUGGESTIONS[0], "Risk window?", "Biggest risks?", "Portfolio weights?", "Stress result?")
    return SUGGESTIONS


# Specific questions take precedence over generic phrases such as "portfolio risk".
TOPICS = (
    ("resilience", r"resilien|break.even|how much.*(?:rise|fall|drop)|cost ceiling"),
    ("drivers", r"attribution|drives?.*(?:return|risk)|(?:return|risk) drivers|contribut"),
    ("stability", r"stabil|turnover|weight change|why.*optimi[sz]er.*chang"),
    ("reconsider", r"reconsider|approve|approval|invest for real|live deployment|what.*stop|reject the process|not invest|suitab"),
    ("signal", r"economic signal|credit signal|credit spread|baa10y|alfred"),
    ("stress", r"stress|adverse|downside scenario|shock"),
    ("frontier", r"frontier"),
    ("history", r"historical.*(expected|forecast|forward)|(?:expected|forecast|forward).*historical|realized return"),
    ("models", r"classroom.*etf|etf.*classroom|models differ|model difference"),
    ("window", r"(?:36|60)[ -]?month|covariance window|estimation window|historical window|risk window|lookback"),
    ("decision", r"committee|reject|\bpilot\b|decision"),
    ("ceiling", r"ceiling|(?:maximum|max|highest|best possible|feasible|achievable).*return|(?:return|target|objective).*feasib"),
    ("allocation", r"allocat(?:ion|ions|ed)|(?:asset|portfolio|holding) weights|holdings|(?:dollars|percentage|percent).*each (?:asset|holding)"),
    ("constraints", r"constraint|violat|compliance|compliant|restriction|\bbind|breach"),
    ("diversification", r"diversifi|correlation|co.movements?"),
    ("cost", r"expenses?|annual cost|fees?|costs?|basis points"),
    ("optimization", r"optimi[sz]|minimum.variance|minimi[sz]e volatil"),
    ("target", r"target|objective|(?:gross|net|expected|annual) return|headroom|shortfall|return goal|return can i expect"),
    ("mandate", r"mandate|horizon|portfolio value|account value|how long|rebalanc|liquid reserve"),
    ("risk", r"\brisks?\b|volatilit|standard deviation"),
)
UNSUPPORTED = "I can explain the active BoilerPortfolio scenario. Try asking about return feasibility, mandate checks, or the selected stress scenario."


def answer_question(question, context, signal, requested, challenge=None, *, stress_failed=False, source_rejected=False, etf_note=None):
    query = re.sub(r"[^\w\s-]", " ", question.casefold())
    query = " ".join(query.split())
    if re.search(r"\b(?:weather|recipe|poem|ignore instructions|crypto|bitcoin)\b|"
                 r"\b(?:buy|sell|trade|execute)\s+(?:me\s+)?\d+|"
                 r"\b(?:what|which) (?:stocks?|ticker|fund) (?:should|to)\b", query):
        return UNSUPPORTED
    if etf_note and re.search(r"actual (?:project 2 |proposed )?(?:etf|universe)|project 2 universe|etf.*(?:fail|reject|shortfall)", query):
        return (etf_note + " Reconsider only when defensible assumptions support a feasible, robust and suitable "
                "allocation and the required implementation evidence and authorization are in place.")
    topic = next((name for name, pattern in TOPICS if re.search(pattern, query)), None)
    if topic is None:
        return UNSUPPORTED

    active, mandate = context.active, context.mandate
    ceiling = context.analysis.max_net_return
    no_mix = "There is no active allocation. " + context.analysis.decision
    if topic in ("decision", "reconsider"):
        brief = investment_brief(context, signal, requested)
        if topic == "reconsider":
            stops = monitoring_rows(context, signal)[0]
            return (f"Current action: **{brief.action}**, with **${brief.capital:,.0f} live**. "
                    f"The net ceiling must reach {context.mandate.target:.2%}. {stops[-1]} "
                    "Reject weights that breach a hard restriction and stop on invalid inputs. "
                    f"{brief.approval_gap} Assign evidence owners before seeking a separate approval.")
        finding = brief.findings[0]
        return f"**{brief.action}**. {brief.ask} {finding.evidence} {finding.implication} Process: {brief.process}"
    if topic == "signal":
        if signal is None:
            disposition, reason = signal_admission(signal, source_rejected=source_rejected)
            return f"The BAA10Y credit signal is unavailable. **{disposition}** · {reason}"
        change = f" The spread changed {signal.change_pp * 100:+.0f} bp." if signal.change_pp is not None else ""
        latest = f" Latest eligible observation: {signal.history[-1].observation_date}." if signal.history else ""
        disposition, rationale = signal_admission(signal)
        return (f"**{disposition}** · {signal.status}. {signal.explanation}{change}{latest} "
                f"{rationale} The signal informs monitoring and leaves portfolio weights unchanged.")
    if topic == "stress":
        if stress_failed:
            return "The selected Lab stress could not be evaluated. Check the stress inputs in Performance and Risk Lab."
        return adverse_summary(context, signal, requested, challenge)
    if topic == "resilience":
        evidence = resilience(context)

        def bp(value):
            return "unavailable" if value is None else f"{value * 10000:+.1f} bp"

        equity = "a feasible mix needs no equity" if evidence.equity_independent else bp(evidence.feasible_equity_cut)
        return (f"Annual cost break-even: held **{bp(evidence.held_cost_break_even)}**, any feasible mix "
                f"**{bp(evidence.feasible_cost_break_even)}**. A negative cost threshold means the objective "
                "is infeasible even at zero recurring cost. Break-even equity return cut: "
                f"held **{bp(evidence.held_equity_cut)}**, reoptimized **{equity}**. "
                "Only the specified forecast or cost changes. A negative cut means an uplift is needed. "
                "These boundaries are proposed monitoring inputs for student review.")
    if topic == "stability":
        if stress_failed or challenge is None:
            return "Run a valid stress in the Risk Lab using the active scenario to compare held and reoptimized weights."
        after = challenge.analysis.portfolios
        candidate = after[2] if len(after) == 3 else None
        if candidate is None:
            return challenge.analysis.decision + " There is no successor allocation for a turnover calculation."
        trade = transition(active, candidate, mandate.portfolio_value, challenge.trade_rate)
        if trade is None:
            return "A stressed candidate is feasible, but there is no starting allocation for a turnover calculation."
        index = trade.largest_index
        driver = context.asset_names[index]
        change = trade.changes[index]
        moved = "rises" if change >= 0 else "falls"
        effect = ""
        if challenge.held:
            held = challenge.held
            effect = (f" Held weights give {held.net_return:.2%} net ({held.verdict}). The reoptimized mix "
                      f"gives {candidate.net_return:.2%} net with {(candidate.volatility-held.volatility)*100:+.2f} pp "
                      "volatility versus holding. The solver targets the lowest risk subject to the challenged constraints.")
        action = decision_for(context, signal, requested, analysis=challenge.analysis).action
        return (f"{challenge.label}: one-way turnover is **{trade.one_way_share:.2%}** and gross trading is "
                f"**{trade.gross_share:.2%}**. {driver} {moved} {abs(change)*100:.2f} pp."
                f"{effect} The stressed reoptimization leads to **{action}**.")
    if topic == "frontier":
        return ("The efficient frontier shows the lowest modeled annual volatility for each displayed net return "
                "under the modeled allocation rules. The active covariance matrix determines its shape. "
                "The Risk Lab plots the active mix and benchmarks alongside it.")
    if topic == "history":
        return ("Historical returns describe realized sample performance. Expected returns are forward assumptions used "
                "to estimate future outcomes. The ETF model uses historical covariance for risk and separate forward "
                "returns for feasibility. The classroom model uses illustrative inputs for both.")
    if topic == "models":
        return (f"The active model is **{context.model}**. The classroom uses illustrative returns and covariance, "
                "with a fictional company sleeve for concentration testing. The reviewed model uses four ETFs, "
                "separate forward expected returns, historical covariance and provisional ETF eligibility rules.")
    if topic == "window":
        if context.model != ETF:
            return "The classroom uses illustrative covariance. The 36- and 60-month historical risk windows apply to a reviewed ETF snapshot."
        if active is None:
            return f"The active ETF window is {context.window} months. {no_mix}"
        rates = [portfolio_metrics(active.weights, context.gross_returns, w.annual_covariance, context.annual_cost)[2]
                 for w in context.windows]
        return (f"The active {context.window}-month window gives **{active.volatility:.2%}** volatility. "
                f"At the same weights, the 36-month estimate is {rates[0]:.2%} and the 60-month estimate is {rates[1]:.2%}.")
    if topic == "mandate":
        return (f"Portfolio value **${mandate.portfolio_value:,.0f}**, horizon **{mandate.horizon} years**, "
                f"and annual net target **{mandate.target:.2%}**. The floors are {mandate.min_bonds:.2%} IG bonds, "
                f"{mandate.min_reserve:.2%} reserve and {mandate.min_five_day:.2%} five-day redemption. "
                f"The nonexempt company cap is {mandate.max_company:.2%}. Long-only, annual rebalancing, no borrowing, "
                "shorting or derivatives. Annual loss tolerance remains unresolved.")
    if topic == "ceiling":
        if ceiling is None:
            return "No modeled return ceiling is available. " + context.analysis.decision
        return (f"The maximum modeled annual net return is **{ceiling:.2%}** versus the **{mandate.target:.2%}** target "
                f"({(ceiling - mandate.target) * 1e4:+.1f} bp headroom). The ceiling uses modeled constraints "
                "and forward assumptions. Instrument eligibility still requires verification.")
    if topic == "cost":
        return (f"Recurring modeled expenses are **{context.annual_cost:.2%}** annually, or about "
                f"**${mandate.portfolio_value * context.annual_cost:,.0f}** at the current portfolio value. "
                "The Lab reports one-time trading costs separately.")
    if topic == "optimization":
        candidate = context.optimized
        if candidate is None:
            return context.analysis.decision
        return (f"The constrained optimum has **{candidate.net_return:.2%}** expected annual net return and "
                f"**{candidate.volatility:.2%}** annual volatility. Its verdict is **{candidate.verdict}**. "
                f"The active mix is **{active.name}**.")
    if active is None:
        return no_mix
    if topic == "allocation":
        return f"**{active.name}** · ${mandate.portfolio_value:,.0f} total\n\n" + "\n".join(
            f"- {asset}: **{weight:.2%}** · ${weight * mandate.portfolio_value:,.0f}"
            for asset, weight in zip(context.asset_names, active.weights))
    if topic == "constraints":
        failures = [rule.name for rule in active.rules if rule.status == "Fail"]
        pending = [rule.name for rule in active.rules if rule.status == "Unverified"]
        return (f"Verdict: **{active.verdict}**. Failed checks: {', '.join(failures) or 'none'}. "
                f"At modeled limits: {', '.join(binding_checks(context)) or 'none'}. "
                f"Unverified: {', '.join(pending) or 'none'}.")
    if topic == "target":
        margin = active.net_return - mandate.target
        status = "meets" if margin >= -TOL else "misses"
        return (f"The active mix **{status}** the **{mandate.target:.2%}** annual net target "
                f"({margin * 1e4:+.1f} bp). Modeled gross return is **{active.net_return + context.annual_cost:.2%}**, "
                f"and modeled net return is **{active.net_return:.2%}**.")
    if topic == "diversification":
        assumed = sum(w * s for w, s in zip(active.weights, context.risk.diagonal() ** .5))
        return (f"The mix has **{active.volatility:.2%} volatility**. It would have **{assumed:.2%}** "
                "annual volatility if all holdings moved in perfect positive correlation at their current individual risks.")
    result = attribution(active.weights, context.gross_returns, context.risk, context.annual_cost)
    if topic == "drivers":
        return driver_summary(context, result)
    brief = investment_brief(context, signal, requested)
    risk = next((item for item in brief.findings if item.question == "Where is the risk concentrated?"), None)
    finding = f" {risk.evidence} {risk.action}" if risk else ""
    stress = (f" Under {challenge.label}, holding the weights changes volatility by "
              f"{(challenge.held.volatility-active.volatility)*100:+.2f} pp."
              if challenge and challenge.held and challenge.label != "Base case" else
              " " + adverse_summary(context, signal, requested) if not stress_failed else
              " The selected stress is invalid and cannot support a risk conclusion.")
    return (f"Modeled annual volatility is **{active.volatility:.2%}**. "
            "The largest positive contributors to modeled variance also drive modeled volatility."
            f"{finding}{stress}")
