"""Use the reviewed ETF evidence in the existing committee workflow."""

import pandas as pd
import streamlit as st

from src.briefing import scenario_row, stress_finding
from src.committee import decision_for
from src.etf_evidence import FORWARD, FORWARD_NOTE
from src.etf_portfolio import analyze_windows, downside_returns, evaluate_etf, snapshot_date
from src.judgment import StressChallenge
from src.historical import TICKERS
from src.portfolio import Analysis, Portfolio, Rule
from src.stress_view import show_stress_comparison

ETF_PENDING = ("ETF bond and reserve eligibility", "Issuer concentration and fund exemptions",
               "Derivatives and leverage", "Five-business-day redemption", "Annual rebalancing implementation",
               "Client annual loss tolerance")


def reviewed_panel(sample):
    return (sample is not None and sample.metadata.get("provider") == "Alpha Vantage"
            and sample.metadata.get("reviewed_panel_sha256") == sample.csv_hash and not sample.warnings)


def etf_candidate(name, case, mandate=None):
    rules = tuple(Rule(rule, "Fail" if rule in case.modeled_failures else "Pass",
                       "Provisional model check. ETF eligibility still requires review.")
                  for rule in ("Modeled IG bond floor", "Modeled reserve floor",
                               "Expected net return target"))
    pending = tuple(Rule(rule, "Unverified", "Requires independent mandate evidence.") for rule in ETF_PENDING
                    if rule != "Five-business-day redemption" or mandate is None or mandate.min_five_day > 0)
    if mandate is not None and mandate.min_five_day == 0:
        pending += (Rule("Five-business-day redemption", "Pass", "No minimum in this scenario."),)
    weights = (Rule("Fully invested and long-only weights", "Pass",
                    "The evaluated weights are nonnegative and sum to 100%. "
                    "Fund leverage and derivatives need separate evidence."),)
    return Portfolio(name, case.weights, case.net_return, case.volatility, weights + rules + pending)


def decision_case(window, mandate=None):
    return Analysis(tuple(etf_candidate(name, case, mandate) for name, case in window.portfolios.items()),
                    window.max_net_return, window.decision, ())


def portfolio_table(windows):
    return pd.DataFrame([
        {"Window": f"{result.months} months", "Portfolio": name, "Net return": f"{case.net_return:.2%}",
         "Volatility": f"{case.volatility:.2%}", "Verdict": case.verdict,
         "Modeled failures": ", ".join(case.modeled_failures),
         **{ticker: f"{weight:.2%}" for ticker, weight in zip(TICKERS, case.weights)}}
        for result in windows for name, case in result.portfolios.items()
    ])


def etf_stress_view(context, signal, requested):
    sample, mandate, active, months = context.sample, context.mandate, context.active, context.window
    st.subheader("Stress overview")
    st.caption("Decision model: reviewed ETF historical covariance · 36- and 60-month windows.")
    basis = FORWARD_NOTE.split("Deduct", 1)[0].strip()
    st.write(basis)
    shock = st.number_input("LQD and VT adverse return reduction (pp)", min_value=0.0,
                            max_value=20.0, value=1.0, step=.25, key="etf_risk_shock")
    st.caption("Applies to LQD and VT forward returns. Both cases retain their ETF covariance estimates, "
               f"the active {context.annual_cost * 10000:g} bp investor cost and the active mandate.")
    cutoff = snapshot_date(sample)
    base = context.windows
    stressed = analyze_windows(sample, mandate, cutoff, downside_returns(FORWARD, shock / 100),
                               context.annual_cost, reviewed=True)
    index = 0 if months == 36 else 1
    adverse = decision_case(stressed[index], mandate)
    held = None
    if active is not None:
        stressed_case = evaluate_etf(active.weights, mandate, downside_returns(FORWARD, shock / 100),
                                     context.annual_cost, stressed[index].annual_covariance)
        held = etf_candidate("Keep active weights", stressed_case, mandate)
    label = f"LQD and VT return reduction: {shock:.2f} percentage points"
    challenge = StressChallenge(label, adverse, held, mandate.target, None)
    st.markdown(stress_finding(active, context.analysis.max_net_return, mandate.target, challenge,
                               decision_for(context, signal, requested, analysis=adverse)))
    show_stress_comparison([
        scenario_row("Base case", f"Reviewed ETF model · {months} months", context, context.proposal,
                     active, None, signal, requested, reference=True),
        scenario_row("ETF downside", label, context, adverse, held, None, signal, requested),
    ], mandate.target)
    with st.expander("Feasibility by ETF risk window"):
        st.dataframe(pd.DataFrame([
            {"Case": case, "Window": window.months, "Net target": f"{mandate.target:.2%}",
             "Modeled maximum": f"{window.max_net_return:.2%}" if window.max_net_return is not None else "Unavailable"}
            for case, windows in (("Reference", base), ("Downside", stressed)) for window in windows
        ]), hide_index=True)
    with st.expander("Base ETF portfolios"):
        st.dataframe(portfolio_table(base), hide_index=True)
    with st.expander("Adverse ETF portfolios"):
        st.dataframe(portfolio_table(stressed), hide_index=True)
    return challenge
