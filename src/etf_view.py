"""Reviewed ETF decision analysis, separate from the classroom engine."""

from dataclasses import asdict
import json

import pandas as pd
import streamlit as st

from src.assumptions import ANNUAL_COST
from src.etf_decision_view import reviewed_panel
from src.etf_evidence import FORWARD, FORWARD_NOTE
from src.etf_portfolio import analyze_windows, downside_returns, snapshot_date
from src.historical import TICKERS


def etf_view(sample, mandate, reviewed):
    st.subheader("ETF portfolio decision analysis")
    st.caption("Historical covariance with separately entered forward returns · Provisional mandate classification. "
               "Changes here are research sensitivities; the executive ETF model retains the documented base inputs.")
    with st.expander("Set up the 36- and 60-month analysis"):
        st.write("Use Treasury yield/carry for BIL and IEF, credit carry less expected loss for LQD, "
                 "and dividend yield plus growth and valuation assumptions for VT. Enter annual arithmetic "
                 "returns after fund expenses and before investor-level costs. Record the sources and rationale.")
        st.write("The model provisionally counts IEF and LQD as investment-grade bonds and BIL as reserve. "
                 "Issuer exemptions, five-day redemption and actual eligibility are unverified.")
        published = reviewed_panel(sample)
        rationale = st.text_area("Dated forward-return sources and rationale",
                                 value=FORWARD_NOTE if published else "")
        decision_date = snapshot_date(sample)
        st.write(f"Common decision date **{decision_date}** · New York date of source capture")
        columns = st.columns(4)
        gross = [col.number_input(f"{ticker} forward return (%)", value=rate * 100 if published else None, min_value=-99.99,
                                  max_value=100.0, step=.25) for col, ticker, rate in zip(columns, TICKERS, FORWARD)]
        cost = st.number_input("Annual investor cost (bp)", min_value=0.0, value=ANNUAL_COST * 10000,
                               max_value=10000.0, step=5.0)
        shock = st.number_input("LQD and VT adverse return reduction (pp)", min_value=0.0,
                                max_value=20.0, value=1.0, step=.25,
                                help="Hypothetical sensitivity. Risk and costs stay fixed.")
        if not reviewed or not rationale.strip() or any(value is None for value in gross):
            st.info("Analysis unavailable until the panel is reviewed and all return assumptions are documented.")
            return
        try:
            base = analyze_windows(sample, mandate, decision_date, [x / 100 for x in gross], cost / 10000,
                                   reviewed=True)
        except (ValueError, ArithmeticError) as error:
            st.error(f"ETF analysis stopped. {error}")
            return
        try:
            adverse = analyze_windows(sample, mandate, decision_date,
                                      downside_returns([x / 100 for x in gross], shock / 100), cost / 10000, reviewed=True)
        except (ValueError, ArithmeticError) as error:
            adverse = ()
            st.warning(f"Adverse sensitivity unavailable. {error}")
        st.caption("Both windows use the same capture date, universe, assumptions and fees. The panel is a "
                   "retrieved snapshot. It does not support earlier decision-date replay.")
        rows = []
        for label, results in (("Base", base), ("Adverse", adverse)):
            for result in results:
                st.write(f"**{label} · {result.months} months ({result.first_price_date} to "
                         f"{result.last_price_date})** · {result.decision}")
                maximum = result.max_net_return
                with st.expander(f"{label} · {result.months}-month annual covariance and risk"):
                    covariance = pd.DataFrame(result.annual_covariance, index=TICKERS, columns=TICKERS)
                    st.dataframe(covariance)
                    st.write({ticker: f"{covariance.loc[ticker, ticker] ** .5:.2%}" for ticker in TICKERS})
                for name, case in result.portfolios.items():
                    rows.append({"Case": label, "Months": result.months, "Portfolio": name,
                                 "Expected net return": f"{case.net_return:.2%}",
                                 "Annual volatility": f"{case.volatility:.2%}",
                                 "Return ceiling": "Unavailable" if maximum is None else f"{maximum:.2%}",
                                 "Ceiling less target": "Unavailable" if maximum is None else
                                 f"{(maximum - mandate.target) * 10000:+.1f} bp",
                                 "Verdict": case.verdict, "Modeled failures": ", ".join(case.modeled_failures),
                                 **{ticker: f"{weight:.2%}" for ticker, weight in zip(TICKERS, case.weights)}})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.write("A covariance change can change volatility and the minimum-risk feasible weights. "
                 "The return ceiling is set by forecasts, costs and modeled mandate limits.")
        record = {"decision_date": decision_date, "sample_sha256": sample.csv_hash,
                  "metadata_sha256": sample.metadata_hash, "forward_returns_percent": dict(zip(TICKERS, gross)),
                  "rationale": rationale, "investor_cost_bp": cost, "adverse_reduction_pp": shock,
                  "mandate": asdict(mandate), "base": [asdict(item) for item in base],
                  "adverse": [asdict(item) for item in adverse]}
        st.download_button("Export ETF analysis evidence", json.dumps(record, default=str, indent=2),
                           "etf-analysis-evidence.json", mime="application/json")
