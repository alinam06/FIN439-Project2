"""Streamlit presentation for local ETF uploads."""

import altair as alt
import pandas as pd
import streamlit as st

from src.etf_view import etf_view
from src.historical import ROLES


def time_series(frame, label, percentage=False, bars=False):
    long = frame.rename_axis("date").reset_index().melt(
        id_vars="date", var_name="Fund", value_name=label
    )
    base = alt.Chart(long)
    marks = base.mark_bar(opacity=.7) if bars else base.mark_line()
    return marks.encode(
        x=alt.X("date:T", title="Observation date"),
        y=alt.Y(f"{label}:Q", axis=alt.Axis(format=".0%" if percentage else "$,.0f")),
        color="Fund:N",
        tooltip=[alt.Tooltip("date:T", format="%Y-%m-%d"), "Fund:N",
                 alt.Tooltip(f"{label}:Q", format=".2%" if percentage else "$,.2f")],
    ).properties(height=275).interactive()


def historical_view(sample, mandate, reviewed, status):
    st.subheader("Historical Market Data")
    st.info("HISTORICAL DATA EXPLORATION · Retrospective ETF statistics for review. "
            "A separate ETF decision analysis is available after review.")
    st.dataframe(pd.DataFrame(list(ROLES.items()), columns=["Ticker", "Candidate fund and role"]),
                 hide_index=True)
    st.caption("Candidate roles require mandate evidence. Provider vintages and historical "
               "decision-date availability remain unverified. Fund-level results exclude "
               "investor-level taxes and transaction costs.")
    if sample is None:
        st.info(f"ETF analysis {status}")
        return
    start, end = sample.sample_dates
    st.write(f"Sample **{start} through {end}** · {len(sample.prices)} aligned closes · "
             f"{len(sample.returns)} monthly returns · USD per share")
    with st.expander("Source metadata and input fingerprints"):
        st.json(sample.metadata)
        st.code(f"Prices SHA-256: {sample.csv_hash}\nMetadata SHA-256: {sample.metadata_hash}")
    if sample.warnings:
        st.warning("Data quality status: review required. The pilot retained every observation.")
        for warning in sample.warnings:
            st.write(warning)
    else:
        st.success("Data quality status: structural checks passed.")
    st.caption("Provider, adjustment method, calendar verification and exclusions are supplied by the uploader. "
               "Reconcile these with the source before committee use.")
    if sample.warnings and not reviewed:
        st.info("Review flagged observations in Advanced Data Management before displaying statistics.")
        return

    st.subheader("Historical risk and return")
    st.dataframe(sample.statistics.style.format("{:.2%}"), width="stretch")
    st.caption("Arithmetic return is monthly mean × 12. Volatility is monthly sample standard "
               "deviation × √12. Drawdown uses monthly closes and is shown as a positive loss magnitude.")
    st.altair_chart(time_series(sample.prices, "Adjusted close"))
    st.altair_chart(time_series(sample.returns, "Monthly return", percentage=True))
    st.altair_chart(time_series(sample.cumulative, "Cumulative return", percentage=True))
    st.subheader("Monthly return correlation")
    heat = sample.correlation.rename_axis("Fund").reset_index().melt(
        id_vars="Fund", var_name="Comparison fund", value_name="Correlation"
    )
    st.altair_chart(alt.Chart(heat).mark_rect().encode(
        x="Fund:N", y="Comparison fund:N",
        color=alt.Color("Correlation:Q", scale=alt.Scale(domain=[-1, 1], scheme="redblue")),
        tooltip=["Fund:N", "Comparison fund:N", alt.Tooltip("Correlation:Q", format=".3f")],
    ).properties(height=280))
    st.caption("Pearson correlation is unitless and unchanged by annualizing covariance. "
               "An undefined correlation is omitted from the heatmap.")
    with st.expander("Annualized sample covariance"):
        st.dataframe(sample.covariance.style.format("{:.6f}"))

    if mandate is not None:
        etf_view(sample, mandate, reviewed)
