"""Allocation and decision evidence drawn from the same modeled portfolios."""

import altair as alt
import pandas as pd
import streamlit as st

from src.judgment import attribution
from src.presentation import CHART_COLORS


def allocation_rows(context, portfolios):
    rows = []
    for portfolio in portfolios:
        stats = attribution(portfolio.weights, context.gross_returns, context.risk, context.annual_cost)
        start = 0.0
        for index, (asset, weight) in enumerate(zip(context.asset_names, portfolio.weights, strict=True)):
            end = start + weight
            rows.append({
                "Portfolio": portfolio.name, "Asset": asset, "Start weight": start, "End weight": end,
                "Start dollars": start * context.mandate.portfolio_value,
                "End dollars": end * context.mandate.portfolio_value,
                "Weight": weight, "Dollars": weight * context.mandate.portfolio_value,
                "Volatility contribution": None if stats.risk_by_asset is None else stats.risk_by_asset[index],
            })
            start = end
    return pd.DataFrame(rows)


def allocation_chart(rows, names, portfolio_value, dollars):
    unit = "dollars" if dollars else "weight"
    axis_format = "$~s" if dollars else ".0%"
    return alt.Chart(rows).mark_bar(orient="horizontal", size=24).encode(
        x=alt.X(f"Start {unit}:Q", stack=None, title="Allocated dollars" if dollars else "Portfolio weight",
                axis=alt.Axis(format=axis_format, tickCount=5),
                scale=alt.Scale(domain=[0, portfolio_value if dollars else 1], nice=False)),
        x2=alt.X2(f"End {unit}:Q"),
        y=alt.Y("Portfolio:N", sort=rows["Portfolio"].drop_duplicates().tolist(), title=None,
                axis=alt.Axis(labelLimit=230, labelPadding=8, ticks=False)),
        color=alt.Color("Asset:N", scale=alt.Scale(domain=list(names), range=list(CHART_COLORS[:len(names)])),
                        legend=alt.Legend(orient="bottom", columns=1, labelLimit=360, title="Holdings")),
        tooltip=["Portfolio", "Asset", alt.Tooltip("Weight:Q", format=".2%"),
                 alt.Tooltip("Dollars:Q", format="$,.0f"),
                 alt.Tooltip("Volatility contribution:Q", format="+.2%", title="Contribution to annual volatility")],
    ).properties(height=alt.Step(46))


def comparison_rows(context, portfolios, segments):
    rows = []
    for portfolio in portfolios:
        own = segments[segments["Portfolio"] == portfolio.name].dropna(subset=["Volatility contribution"])
        if own.empty:
            driver = "Unavailable"
        else:
            top = own.loc[own["Volatility contribution"].idxmax()]
            driver = f"{top['Asset']} ({top['Volatility contribution']*100:+.2f} pp)"
        failures = ", ".join(rule.name for rule in portfolio.rules if rule.status == "Fail")
        margin = (portfolio.net_return - context.mandate.target) * 10000
        rows.append({"Portfolio": portfolio.name, "Expected annual net return": f"{portfolio.net_return:.2%}",
                     "Annual volatility": f"{portfolio.volatility:.2%}", "Margin vs objective": f"{margin:+.1f} bp",
                     "Overall verdict": portfolio.verdict, "Modeled failures": failures or "None",
                     "Largest risk contribution": driver})
    if context.optimized is None:
        rows.insert(2, {"Portfolio": "Constrained portfolio", "Expected annual net return": "—",
                        "Annual volatility": "—", "Margin vs objective": "—",
                        "Overall verdict": "No feasible solution", "Modeled failures": "No candidate to assess",
                        "Largest risk contribution": "—"})
    return pd.DataFrame(rows)


def baseline_tradeoff(context):
    equal, benchmark = context.analysis.portfolios[:2]
    comparison = (f"Versus equal weight, the benchmark changes modeled annual net return by "
                  f"{(benchmark.net_return-equal.net_return)*100:+.2f} pp and volatility by "
                  f"{(benchmark.volatility-equal.volatility)*100:+.2f} pp.")
    failed = [p.name for p in (equal, benchmark) if p.verdict == "Fail"]
    if len(failed) == 2:
        return comparison + " Both baselines fail modeled mandate checks and serve as comparisons only."
    if failed:
        return comparison + f" {failed[0]} fails modeled mandate checks and serves as a comparison only."
    return comparison + " The baselines serve as reference points for the modeled trade-off."


def show_allocation_comparison(context, portfolios):
    st.subheader("Compare allocation choices")
    dollars = st.radio("Allocation display", ("Weights", "Dollar amounts"), horizontal=True) == "Dollar amounts"
    rows = allocation_rows(context, portfolios)
    st.altair_chart(allocation_chart(rows, context.asset_names, context.mandate.portfolio_value, dollars),
                    width="stretch")
    st.caption("Hover over holdings for weights, dollars, and signed contributions to annual volatility.")
    st.dataframe(comparison_rows(context, portfolios, rows), hide_index=True, width="stretch")
    st.write(baseline_tradeoff(context))
    if context.optimized is None:
        st.caption("The constrained row reports feasibility. No allocation bar is drawn without solver weights.")
