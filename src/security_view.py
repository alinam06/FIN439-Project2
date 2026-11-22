"""Offline-first Market Research workspace."""

from datetime import datetime, timedelta, timezone
from time import monotonic

import altair as alt
import pandas as pd
import streamlit as st

from src.keyless_market import fetch_market_history
from src.presentation import CHART_COLORS
from src.security_research import (
    PERIODS, PROFILES, PROXIES, ResearchUnavailable, aligned_history, configured_key, demo_histories, fetch_online,
    historical_metrics, local_history, mandate_notes, ticker_input,
)


def line_chart(values, title, format_string):
    long = values.rename_axis("Date").reset_index().melt(
        id_vars="Date", var_name="Ticker", value_name="Value"
    )
    return alt.Chart(long).mark_line(point=len(values) <= 13).encode(
        x=alt.X("Date:T", title="Observation date"),
        y=alt.Y("Value:Q", title=title, axis=alt.Axis(format=format_string),
                scale=alt.Scale(zero=False)),
        color=alt.Color("Ticker:N", scale=alt.Scale(range=list(CHART_COLORS))),
        tooltip=[alt.Tooltip("Date:T", format="%Y-%m-%d"), "Ticker:N",
                 alt.Tooltip("Value:Q", title=title, format=format_string)],
    ).properties(height=240).interactive()


def profile_card(profile, history, mandate):
    st.subheader(f"{profile.ticker} · {profile.name}")
    st.caption(f"{profile.kind} · {profile.category} · USD")
    st.write(f"**Potential role:** {profile.role}. {profile.characteristic}")
    if history is not None:
        if history.daily_close is not None:
            last = history.daily_close.index[-1].date()
            st.write(f"**Latest completed daily bar close:** ${history.daily_close.iloc[-1]:,.2f} · {last}. "
                     "Includes extended trading hours.")
        elif history.close is None:
            last = history.adjusted.index[-1].date()
            st.write(f"**Latest adjusted observation:** ${history.adjusted.iloc[-1]:,.2f} · {last}. "
                     "Unadjusted close unavailable from this source.")
        else:
            st.write(f"**Latest completed monthly close:** ${history.close.iloc[-1]:,.2f} · "
                     f"{history.close.index[-1].date()}.")
        st.caption(f"{history.source} · Captured {history.captured_at}")
    else:
        st.caption("Latest price, date and historical risk metrics unavailable.")
        proxy = PROXIES.get(profile.ticker)
        if proxy:
            st.write(f"**Illustrative classroom sleeve:** {proxy.gross_return:.2%} expected gross return and "
                     f"{proxy.volatility:.2%} modeled annual volatility. These are classroom inputs.")
    st.write(f"**Mandate eligibility: Unverified.** {mandate_notes(profile, mandate)}")
    st.markdown(f"[Security source]({profile.source})")


def charts(histories, months, *, synthetic=False):
    try:
        prices = aligned_history(histories, months)
    except ResearchUnavailable as error:
        st.warning(str(error))
        return
    growth, drawdown, metrics, corr = historical_metrics(prices)
    price_only = next(iter(histories.values())).basis == "price"
    return_label = "Annualized price change" if price_only else "Annualized total return"
    if price_only:
        metrics = metrics.rename(columns={"Annualized total return": return_label})
        st.caption("Price-only series. Dividends and splits are not adjusted. Corporate actions can distort results.")
    st.caption(f"Common sample {prices.index[0].date()} to {prices.index[-1].date()} · "
               f"{months} monthly returns · {'synthetic USD example' if synthetic else 'USD'}. "
               "Annualized return is geometric. Volatility uses monthly sample standard deviation × √12.")
    st.dataframe(metrics.style.format("{:.2%}"), width="stretch")
    st.subheader("Synthetic monthly values" if synthetic else "Month-end price history")
    for ticker, history in histories.items():
        close = history.close if history.close is not None else history.adjusted
        label = ("Synthetic value" if synthetic else
                 "Unadjusted USD close" if history.close is not None else "Adjusted USD close")
        st.altair_chart(line_chart(close.loc[prices.index].to_frame(ticker), label, "$,.2f"), width="stretch")
    st.subheader("Growth of $100 · Synthetic example" if synthetic else
                 "Growth of $100 · Price-only" if price_only else "Growth of $100 · Distribution-adjusted")
    st.altair_chart(line_chart(growth, "Value of $100", "$,.2f"), width="stretch")
    st.subheader("Synthetic drawdowns" if synthetic else "Historical drawdowns")
    st.altair_chart(line_chart(drawdown, "Drawdown from peak", ".1%"), width="stretch")
    st.subheader("Synthetic risk versus return" if synthetic else "Historical risk versus return")
    points = metrics.rename_axis("Ticker").reset_index()
    st.altair_chart(alt.Chart(points).mark_point(filled=True, size=110).encode(
        x=alt.X("Annualized volatility:Q", axis=alt.Axis(format=".1%")),
        y=alt.Y(f"{return_label}:Q", axis=alt.Axis(format=".1%"), scale=alt.Scale(zero=False)),
        color=alt.Color("Ticker:N", scale=alt.Scale(range=list(CHART_COLORS))),
        tooltip=["Ticker:N", alt.Tooltip(f"{return_label}:Q", format=".2%"),
                 alt.Tooltip("Annualized volatility:Q", format=".2%")],
    ).properties(height=240), width="stretch")
    if len(histories) == 2:
        value = corr.iloc[0, 1]
        if pd.isna(value):
            st.caption("Correlation is unavailable because at least one series has no measured return variation.")
        else:
            st.write(f"**Monthly return correlation: {value:+.2f}.** "
                     + ("Calculated from the hypothetical paths." if synthetic else
                        "The observed relationship can change and does not establish portfolio diversification."))


def security_view(sample, reviewed, mandate):
    st.subheader("Security search")
    st.caption("Research U.S.-listed USD stocks and ETFs. Searches and watchlist entries leave the optimizer unchanged.")
    provider = st.selectbox("Online data source", ("Market History (no key)", "Alpha Vantage", "Offline only"),
                            key="research_provider")
    key = configured_key() if provider == "Alpha Vantage" else ""
    if provider == "Market History (no key)":
        st.caption("Keyless daily price history for your local research. The reviewed ETF panel takes precedence.")
    elif provider == "Alpha Vantage":
        st.caption("Online access configured · Adjusted monthly history." if key else
                   "No Alpha Vantage key detected. The keyless source and local data remain available.")
    with st.form("security_search"):
        left, right = st.columns(2)
        name = left.text_input("Ticker", value="VT", help="Examples: AAPL, NVDA, MSFT, BIL, IEF, LQD, VT.")
        benchmark = right.text_input("Compare with (optional)", help="Enter another security, such as BIL.")
        submitted = st.form_submit_button("Search securities", type="primary")

    if submitted:
        st.session_state["security_demo"] = False
        try:
            ticker = ticker_input(name)
            others = (ticker_input(benchmark),) if benchmark.strip() else ()
            if ticker in others:
                raise ResearchUnavailable("Choose a different comparison ticker.")
        except ResearchUnavailable as error:
            st.session_state.pop("security_query", None)
            st.warning(str(error))
        else:
            st.session_state["security_query"] = (ticker, *others)
            st.session_state["security_query_provider"] = provider
            st.session_state["security_messages"] = {}
            cache = st.session_state.setdefault("security_online_cache", {})
            for symbol in st.session_state["security_query"]:
                if local_history(sample, symbol, reviewed) is not None:
                    continue
                cached = cache.get((provider, symbol))
                if cached and datetime.now(timezone.utc) - datetime.fromisoformat(
                    cached[1].captured_at
                ).astimezone(timezone.utc) < timedelta(hours=6):
                    continue
                try:
                    if provider == "Market History (no key)":
                        now = monotonic()
                        if now - st.session_state.get("market_history_last_request", float("-inf")) < 30:
                            raise ResearchUnavailable("Wait 30 seconds between new keyless history requests, then search again.")
                        st.session_state["market_history_last_request"] = now
                        result = fetch_market_history(symbol)
                    elif provider == "Alpha Vantage" and key:
                        result = fetch_online(symbol, key)
                    else:
                        raise ResearchUnavailable("No online history requested. Choose the keyless source or configure Alpha Vantage.")
                    cache[(provider, symbol)] = result
                except ResearchUnavailable as error:
                    st.session_state["security_messages"][symbol] = str(error)
    if st.button("Try the offline demonstration"):
        st.session_state["security_demo"] = True
    if st.session_state.get("security_demo"):
        st.info("Synthetic demonstration · The hypothetical series are invented and do not represent any traded security.")
        demo_period = st.selectbox("Demonstration window (months)", PERIODS, index=1)
        charts(demo_histories(), demo_period, synthetic=True)
        return
    with st.expander("Research watchlist"):
        st.caption("Browser session only. A watchlist does not authorize or allocate holdings.")
        watchlist = st.session_state.get("security_watchlist", [])
        if watchlist:
            selected = st.selectbox("Watchlist symbol", watchlist)
            if st.button("Remove from watchlist"):
                st.session_state["security_watchlist"] = [symbol for symbol in watchlist if symbol != selected]
                st.rerun()
        else:
            st.caption("Search a supported security to add it.")
    query = st.session_state.get("security_query", ())
    if not query:
        st.caption("Try VT with BIL to compare global equity and short Treasury exposure when the private panel is available.")
        return

    histories = {}
    cache = st.session_state.get("security_online_cache", {})
    messages = st.session_state.get("security_messages", {})
    searched_provider = st.session_state.get("security_query_provider")
    if searched_provider != provider:
        st.info("Showing the previous search. Submit again to use the newly selected source.")
    for ticker in query:
        profile, online_history = cache.get((searched_provider, ticker), (PROFILES.get(ticker), None))
        history = local_history(sample, ticker, reviewed) or online_history
        if ticker in messages:
            cached_note = " Showing the last successful session result." if history is not None else ""
            st.warning(f"{ticker} · {messages[ticker]}{cached_note}")
        if profile is None:
            st.info(f"{ticker} · No profile is available. Try another ticker or data source.")
            continue
        profile_card(profile, history, mandate)
        if st.button(f"Add {ticker} to watchlist", key=f"watch_{ticker}", disabled=ticker in watchlist):
            st.session_state["security_watchlist"] = [*watchlist, ticker]
            st.rerun()
        if history is not None:
            histories[ticker] = history
    if histories:
        choices = (6, 12) if any(history.basis == "price" for history in histories.values()) else PERIODS
        available = []
        for months in choices:
            try:
                aligned_history(histories, months)
            except ResearchUnavailable:
                continue
            available.append(months)
        if not available and len(histories) == 2:
            first = next(iter(histories))
            st.warning(f"The two histories have no supported common window. Showing {first} on its own.")
            histories = {first: histories[first]}
            choices = (6, 12) if histories[first].basis == "price" else PERIODS
            available = [months for months in choices if len(histories[first].adjusted) > months]
        if not available:
            st.warning("Too few matched month-end observations for the selected sources.")
            for ticker, history in histories.items():
                if history.daily_close is not None:
                    st.altair_chart(line_chart(history.daily_close.to_frame(ticker),
                                              "Unadjusted daily bar close", "$,.2f"), width="stretch")
            return
        if len(histories) != len(query):
            st.info("A comparison series is unavailable. Showing the available security only.")
        months = st.selectbox("Historical window (months)", available,
                              index=available.index(36) if 36 in available else 0)
        charts(histories, months)
