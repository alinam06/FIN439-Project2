"""Small evidence panels for the existing investment workflow."""

import pandas as pd
import streamlit as st

from src.judgment import (
    reserve_sensitivity, resilience, restrictions, transition,
)


def show_resilience(context):
    result = resilience(context)
    with st.expander("Break-even thresholds and constraint slack"):
        def threshold(value, *, cost=False):
            if value is None:
                return "Unavailable"
            if cost and value < -1e-10:
                return f"No nonnegative cost meets target ({value * 10000:+.1f} bp algebraic level)"
            return f"{value * 10000:+.1f} bp"

        st.write(f"**Maximum annual recurring cost** · Held {threshold(result.held_cost_break_even, cost=True)} · "
                 f"Any feasible modeled allocation {threshold(result.feasible_cost_break_even, cost=True)}")
        st.caption("Only recurring cost changes. A held return break-even cannot cure a separate failed mandate rule.")
        equity = ("Available mix needs no equity exposure" if result.equity_independent
                  else threshold(result.feasible_equity_cut))
        st.write(f"**Parallel equity return cut at break-even** · Held {threshold(result.held_equity_cut)} · "
                 f"Reoptimized {equity}")
        st.caption("Shift only equity forward returns by the same absolute amount. Other forecasts, costs, risk, "
                   "and mandate stay fixed. A negative cut means an uplift is required. These are modeled boundaries "
                   "for student review, with no extra safety margin.")
        if checks := restrictions(context):
            st.dataframe(pd.DataFrame([{
                "Rule": check.name, "Type": "Investor objective" if check.objective else "Modeled hard limit",
                "Actual": f"{check.exposure:.2%}", "Limit": f"{check.limit:.2%}", "Slack (pp)": f"{check.slack * 100:+.2f}",
                "Verdict": check.status,
            } for check in checks]), hide_index=True)
            pending = [rule.name for rule in context.active.rules if rule.status == "Unverified"]
            if pending:
                st.caption("Unknown or unverified: " + ", ".join(pending) + ".")
        tighter, ceiling = reserve_sensitivity(context)
        if tighter > context.mandate.min_reserve:
            delta = (f" ({(ceiling - context.analysis.max_net_return) * 10000:+.1f} bp vs base)"
                     if ceiling is not None and context.analysis.max_net_return is not None else "")
            modeled = f"{ceiling:.2%}{delta}" if ceiling is not None else "no feasible weights"
            st.caption(f"Hypothetical reserve floor {tighter:.2%} with other inputs fixed: modeled ceiling "
                       f"{modeled}. The active mandate is unchanged.")


def show_stability(context, challenge):
    active, held, stressed = context.active, challenge.held, challenge.analysis
    candidate = stressed.portfolios[2] if len(stressed.portfolios) == 3 else None
    trade = transition(active, candidate, context.mandate.portfolio_value, challenge.trade_rate)
    if trade is not None:
        expense = "unknown" if trade.expense is None else f"${trade.expense:,.2f}"
        st.caption(f"Largest change: {context.asset_names[trade.largest_index]} "
                   f"({abs(trade.changes[trade.largest_index]) * 100:.2f} pp) · One-way turnover "
                   f"{trade.one_way_share:.2%} (${trade.one_way_dollars:,.0f}) · Gross trading "
                   f"{trade.gross_share:.2%} (${trade.gross_dollars:,.0f}) · One-time cost {expense}.")
    if context.windows and (active or candidate):
        with st.expander("Stressed ETF weights"):
            st.dataframe(pd.DataFrame([{
                "Asset": asset, "Starting / held": f"{active.weights[i]:.2%}" if active else "Unavailable",
                "Reoptimized": f"{candidate.weights[i]:.2%}" if candidate else "Unavailable",
            } for i, asset in enumerate(context.asset_names)]), hide_index=True)
