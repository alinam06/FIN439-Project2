"""Risk and stress page within the investment dashboard."""

from dataclasses import replace
import json

import pandas as pd
import streamlit as st

from src.briefing import scenario_row, stress_finding
from src.committee import decision_for, recommendation
from src.judgment import StressChallenge
from src.assumptions import ASSETS
from src.feasibility_view import return_ceiling_chart
from src.stress import (
    PRESETS, StressInputs, assess_stress, candidate, experiment_record, historical_windows, preset,
)


def custom_inputs(base):
    defaults = StressInputs()
    with st.expander("Expected returns and volatility", expanded=True):
        cols = st.columns(3)
        fields = {}
        for column, (key, label) in zip(cols, (("equity", "Equity"), ("bond", "Bonds"), ("cash", "Treasury bill proxy"))):
            fields[f"{key}_shift"] = column.number_input(
                f"{label} expected return shift (pp)", value=0.0, step=.25
            ) / 100
            fields[f"{key}_vol_scale"] = column.number_input(
                f"{label} volatility multiplier", min_value=.01, max_value=10.0, value=1.0, step=.10
            )
    with st.expander("Correlation and costs", expanded=True):
        cols = st.columns(3)
        for column, (key, label) in zip(cols, (
            ("equity_bond_corr", "Global equity / IG fund correlation"),
            ("treasury_bond_corr", "Treasury note / IG fund correlation"),
            ("equity_company_corr", "Global equity / fictional stock correlation"),
        )):
            fields[key] = column.number_input(label, min_value=-1.0, max_value=1.0,
                                               value=getattr(defaults, key), step=.05)
        left, right = st.columns(2)
        fields["annual_cost"] = left.number_input(
            "Recurring annual expense (bp)", 0.0, 10000.0, defaults.annual_cost * 10000, step=5.0
        ) / 10000
        fields["trade_cost"] = right.number_input(
            "One-time cost per dollar traded (bp)", 0.0, 10000.0, 0.0, step=5.0
        ) / 10000
    with st.expander("Challenged mandate", expanded=True):
        cols = st.columns(4)
        limits = {}
        for column, (key, label) in zip(cols, (
            ("min_bonds", "Minimum IG bonds (%)"), ("min_reserve", "Minimum reserve (%)"),
            ("max_company", "Maximum company (%)"), ("target", "Net target (%)"),
        )):
            limits[key] = column.number_input(label, -99.99 if key == "target" else 0.0,
                                               100.0, getattr(base, key) * 100, step=.25) / 100
    return StressInputs(**fields), replace(base, **limits)


def show_historical(sample, reviewed):
    st.subheader("Historical estimation windows")
    st.caption("Retrospective ETF risk estimates. These results do not enter the classroom optimizer.")
    status, windows = historical_windows(sample, reviewed=reviewed)
    st.info(status)
    if windows:
        st.dataframe(pd.DataFrame({f"{size} months": item[2].map("{:.2%}".format)
                                   for size, item in windows.items()}))
        for size, (first, last, _, risk, correlations) in windows.items():
            with st.expander(f"{size} months · return dates {first} to {last}"):
                st.write("Annualized sample covariance")
                st.dataframe(risk)
                st.write("Monthly return correlations")
                st.dataframe(correlations)


def format_rate(value, *, delta=False):
    if value is None:
        return "Unavailable"
    return f"{value * 10000:+.1f} bp" if delta else f"{value:.2%}"


def show_classroom_overview(context, signal, requested):
    st.subheader("Stress overview")
    base = context.mandate
    cases = [scenario_row("Base case", PRESETS["Base case"], context, context.proposal,
                          context.active, None, signal, requested, reference=True)]
    for name, assumption in PRESETS.items():
        if name == "Base case":
            continue
        inputs, mandate = preset(name, base)
        result = assess_stress(base, mandate, inputs, active=context.active)
        cases.append(scenario_row(name, assumption, context, result.stressed, result.held,
                                  inputs.trade_cost, signal, requested, target=mandate.target))
    show_stress_comparison(cases, base.target)
    adverse = [(row["Scenario"], row["_ceiling"]) for row in cases[1:] if row["_ceiling"] is not None]
    if adverse:
        label, ceiling = min(adverse, key=lambda item: item[1])
        st.caption(f"Lowest ceiling: {label}, {ceiling:.2%}. "
                   + ("Set aside target-infeasible proposals." if ceiling < base.target else "Check the held weights under each scenario."))


def show_stress_comparison(cases, target):
    frame = pd.DataFrame(cases)
    caps = [row["_ceiling"] for row in cases]
    frame = frame.drop(columns="_ceiling")
    base = caps[0]
    frame["Change from base"] = [f"{(value-base)*10000:+.1f} bp" if value is not None and base is not None else "—"
                                  for value in caps]
    frame["Gap to target"] = [f"{(value-target)*10000:+.1f} bp" if value is not None else "—" for value in caps]
    st.dataframe(frame, hide_index=True, width="stretch", column_order=[
        "Scenario", "Modeled maximum", "Change from base", "Gap to target", "Committee action",
    ])
    short_names = {
        "Equity market deterioration": "Equity weakness",
        "Higher investment costs": "Higher costs",
        "Rising stock/bond correlation": "Higher correlation",
        "Increased liquidity requirement": "Higher reserve floor",
        "Combined adverse scenario": "Combined stress",
    }
    labels = [short_names.get(label, label) for label in frame["Scenario"]]
    st.altair_chart(return_ceiling_chart(list(zip(labels, caps)), target), width="stretch")


def show_stress(base, stressed, result):
    original = candidate(result.base)
    rows = (("Starting allocation", original), ("Held under stress", result.held),
            ("Reoptimized under stress", result.candidate))
    with st.expander("Selected scenario calculations"):
        st.dataframe(pd.DataFrame([
            {"Portfolio": label, "Annual net return": format_rate(p.net_return if p else None),
             "Annual volatility": format_rate(p.volatility if p else None),
             "Mandate verdict": p.verdict if p else "Unavailable"} for label, p in rows
        ]), hide_index=True)
        st.dataframe(pd.DataFrame([
            {"Case": label, "Net target": format_rate(mandate.target),
             "Modeled maximum": format_rate(analysis.max_net_return),
             "Headroom / shortfall": format_rate(analysis.max_net_return - mandate.target
                                                 if analysis.max_net_return is not None else None, delta=True)}
            for label, mandate, analysis in (("Starting", base, result.base), ("Challenged", stressed, result.stressed))
        ]), hide_index=True)
        if original or result.candidate:
            st.dataframe(pd.DataFrame([
                {"Asset": asset.name,
                 "Starting and held weight": format_rate(original.weights[i] if original else None),
                 "Reoptimized weight": format_rate(result.candidate.weights[i] if result.candidate else None)}
                for i, asset in enumerate(ASSETS)
            ]), hide_index=True)


def stress_view(base, *, active=None, requested="PILOT"):
    name = st.selectbox("Stress scenario", (*PRESETS, "Custom stress"), key="stress_preset")
    try:
        if name == "Custom stress":
            inputs, stressed = custom_inputs(base)
        else:
            st.write(PRESETS[name])
            inputs, stressed = preset(name, base)
        result = assess_stress(base, stressed, inputs, active=active)
    except (ValueError, ArithmeticError) as error:
        st.error(f"Stop. The stress case could not be evaluated. {error}")
    else:
        if name != "Base case":
            challenge = StressChallenge(name, result.stressed, result.held, stressed.target, inputs.trade_cost)
            st.markdown(stress_finding(candidate(result.base), result.base.max_net_return, base.target, challenge,
                                       recommendation(result.stressed, requested=requested, illustrative=True)))
        if name != "Base case":
            show_stress(base, stressed, result)
        record = experiment_record(name, base, stressed, inputs, result, active=active)
        st.download_button("Export before-and-after results", json.dumps(record, indent=2, allow_nan=False),
                           "stress-experiment.json", mime="application/json")
        return StressChallenge(name, result.stressed, result.held, stressed.target, inputs.trade_cost)
    return None
