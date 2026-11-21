"""Streamlit investment dashboard for the FIN 439 committee case."""

from dataclasses import replace

import altair as alt
import pandas as pd
import streamlit as st

from src.analyst_view import show_analyst
from src.allocation_view import show_allocation_comparison
from src.assumptions import ANNUAL_COST, ASSETS, CORRELATIONS, DATASET
from src.briefing import investment_brief, project_etf_finding
from src.briefing_view import committee_briefing, dashboard, reviewed_etf_access
from src.committee import ACTIONS, decision_for, weight_ranges
from src.etf_decision_view import etf_stress_view, portfolio_table, reviewed_panel
from src.historical_view import historical_view
from src.investment_context import CLASSROOM, ETF, build_context
from src.investment_views import (
    active_history, committee_sections, committee_summary, fund_explorer, simulator,
)
from src.etf_portfolio import snapshot_date
from src.judgment_view import show_resilience, show_stability
from src.portfolio import Mandate, portfolio_metrics
from src.presentation import (
    ANALYST, BUILDER, CHART_COLORS, COMMITTEE, DARK_GOLD, DASHBOARD, INK, PAGES,
    RESEARCH, RISK,
)
from src.security_view import security_view
from src.signal_view import signal_view
from src.stress_view import show_classroom_overview, show_historical, stress_view
from src.workspace_view import experiment_view, workspace_controls

INPUT_KEYS = ("value", "horizon", "target", "bonds", "reserve", "company", "redemption")


def reset_scenario():
    st.session_state["scenario_mode"] = "Default client"
    st.session_state.pop("reviewed_stress", None)
    st.session_state.pop("scenario_etf_cost_bp", None)
    for model in (CLASSROOM, ETF):
        st.session_state.pop(f"custom_mix_{model}", None)
    st.session_state.weight_editor_revision = st.session_state.get("weight_editor_revision", 0) + 1
    for key in INPUT_KEYS:
        st.session_state.pop(f"scenario_{key}", None)


def scenario_inputs(default, *, inline=False):
    panel = st.expander("Scenario and mandate", expanded=True) if inline else st.sidebar
    with panel:
        st.subheader("Client scenario")
        mode = st.radio("Analysis mode", ("Default client", "Custom scenario"), key="scenario_mode")
        if mode == "Default client":
            st.write("Age 45 · Retirement at 60")
            st.caption("Lab 13 · 15-year horizon · Annual rebalancing")
            return default

        st.button("Reset to default", on_click=reset_scenario)

        def percent(key, label, value, minimum=0.0, help_text=None):
            return st.number_input(label, minimum, 100.0, value * 100,
                                   step=0.1, format="%.2f", key=f"scenario_{key}", help=help_text) / 100

        with st.expander("Portfolio and objective", expanded=True):
            value = st.number_input("Portfolio value ($)", min_value=1.0, value=default.portfolio_value,
                                    step=50_000.0, key="scenario_value")
            horizon = st.number_input("Investment horizon (years)", 1, 100, default.horizon,
                                      key="scenario_horizon")
            target = percent("target", "Annual net return target (%)", default.target, -99.99)
        with st.expander("Mandate limits", expanded=False):
            bonds = percent("bonds", "Minimum investment-grade bonds (%)", default.min_bonds)
            reserve = percent("reserve", "Minimum liquid reserve (%)", default.min_reserve)
            company = percent("company", "Maximum individual company (%)", default.max_company,
                              help_text="Diversified funds and U.S. Treasury securities are exempt.")
            redemption = percent("redemption", "Minimum five-day redeemable share (%)", default.min_five_day,
                                 help_text="Changes the requirement shown in compliance. Redemption evidence is unverified.")
        return Mandate(value, horizon, target, bonds, reserve, company, redemption)


def model_label(context):
    if context.model == ETF:
        return (f"Reviewed ETF snapshot · {context.window}-month historical covariance · "
                f"captured {snapshot_date(context.sample)} · separate forward assumptions")
    return "Training and validation · Illustrative classroom assumptions"


def compared(context):
    result = context.analysis
    if context.active and context.active not in result.portfolios:
        return replace(result, portfolios=result.portfolios + (context.active,))
    return result


def risk_chart(result, target):
    points = pd.DataFrame([
        {"Portfolio": portfolio.name, "Volatility": portfolio.volatility, "Net return": portfolio.net_return,
         "Mandate verdict": portfolio.verdict}
        for portfolio in result.portfolios
    ])
    frontier = pd.DataFrame(result.frontier, columns=["Volatility", "Net return"])
    x = alt.X("Volatility:Q", title="Modeled annual volatility", axis=alt.Axis(format="%"))
    y = alt.Y("Net return:Q", title="Expected annual net return",
              axis=alt.Axis(format="%"), scale=alt.Scale(zero=False))
    metrics = [alt.Tooltip("Volatility:Q", format=".2%"), alt.Tooltip("Net return:Q", format=".2%")]
    curve = alt.Chart(frontier).mark_line(color=DARK_GOLD, strokeWidth=3).encode(
        x=x, y=y, order="Net return:Q", tooltip=metrics
    )
    dots = alt.Chart(points).mark_point(filled=True, size=145).encode(
        x=x, y=y,
        color=alt.Color("Portfolio:N", scale=alt.Scale(domain=[p.name for p in result.portfolios],
                        range=list(CHART_COLORS)), legend=alt.Legend(orient="bottom")),
        shape=alt.Shape("Mandate verdict:N", scale=alt.Scale(domain=["Fail", "Unverified", "Pass"],
                        range=["cross", "diamond", "circle"]), legend=alt.Legend(orient="bottom")),
        tooltip=["Portfolio:N", "Mandate verdict:N", *metrics],
    )
    level = alt.Chart(pd.DataFrame({"Net return": [target], "Label": [f"Required net return {target:.2%}"]}))
    line = level.mark_rule(color=INK, strokeWidth=2, strokeDash=[5, 4]).encode(
        y=y, tooltip=[alt.Tooltip("Net return:Q", title="Required net return", format=".2%")])
    label = level.mark_text(align="left", baseline="bottom", dy=-5, color=INK, fontWeight="bold").encode(
        x=alt.value(8), y=y, text="Label:N")
    return alt.layer(line, curve, dots, label).properties(height=325, padding={"top": 20}).interactive()


def portfolio_analysis(context):
    result = compared(context)
    st.subheader("Risk and allocation comparison")
    st.caption(model_label(context))
    st.altair_chart(risk_chart(result, context.mandate.target), width="stretch")
    show_allocation_comparison(context, result.portfolios)


def compliance(result):
    st.header("Mandate Compliance and Methodology")
    st.write("A failed modeled rule produces **Fail**. A mix with passing modeled rules and missing "
             "evidence receives **Unverified**.")
    st.dataframe(pd.DataFrame([
        {"Rule": rule.name, "Portfolio": p.name, "Status": rule.status, "Evidence": rule.detail}
        for p in result.portfolios for rule in p.rules
    ]), hide_index=True)
    st.subheader("Classroom assumptions")
    st.write(DATASET)
    st.dataframe(pd.DataFrame([
        {"Asset": asset.name, "Gross annual return": f"{asset.gross_return:.2%}",
         "Annual volatility": f"{asset.volatility:.2%}", "Bond eligible": asset.investment_grade,
         "Reserve eligible": asset.reserve_eligible,
         "Modeled issuer": asset.company or "Exempt sleeve"}
        for asset in ASSETS
    ]), hide_index=True)
    with st.expander("Annual correlation matrix"):
        names = [asset.name for asset in ASSETS]
        st.dataframe(pd.DataFrame(CORRELATIONS, index=names, columns=names))
    with st.expander("Model and eligibility notes"):
        st.write(f"Net return is the weighted annual gross return less {ANNUAL_COST:.2%} in illustrative "
                 "annual costs. Volatility uses the full covariance matrix. Taxes, trading costs, "
                 "and cash flows are outside this model.")
        st.write("The optimization applies the modeled weight, bond, reserve, company and net return "
                 "rules. Five-day redemption requires actual redemption evidence. Portfolio value "
                 "affects dollar allocations, and the horizon affects target compounding.")
        st.write("The 10-year Treasury note contributes to both modeled minimums. They test different attributes "
                 "of the same holding, so the weights still sum to 100%. Reserve treatment is a classroom "
                 "assumption about saleability. Duration risk remains, and the five-day redemption rule requires "
                 "separate evidence. An ETF wrapper such as IEF needs its own eligibility review.")
        st.write("The fictional stock is a classroom-only position that exercises the individual-company cap. "
                 "It does not enter the historical ETF universe.")
        st.write("Historical prices and ALFRED vintages are observations. The classroom expected returns and "
                 "correlations are illustrative assumptions. Synthetic test fixtures verify code behavior.")


def main():
    st.set_page_config(page_title="BoilerPortfolio | Investment Intelligence Platform", layout="wide")
    st.sidebar.title("BoilerPortfolio")
    st.sidebar.caption("Investment Intelligence Platform")
    page = st.sidebar.selectbox("Navigate to", PAGES, key="page")
    st.sidebar.caption("Independent FIN 439 student project")
    try:
        builder_view = None
        if page == BUILDER:
            st.header(BUILDER)
            builder_view = st.selectbox("Builder view", ("Allocation", RESEARCH), key="builder_view")
        mandate = scenario_inputs(Mandate(), inline=page == BUILDER and builder_view == "Allocation")
        st.sidebar.caption(f"{mandate.horizon} years · {mandate.target:.2%} net target · "
                           f"{mandate.min_bonds:.0%} IG bond floor · {mandate.min_reserve:.0%} reserve")
        data, reviewed, signal_date, signal = workspace_controls()
        verified_etf = reviewed_panel(data.etf)
        model = CLASSROOM
        window = 60
        model_key = "decision_model" if verified_etf else None
        prior = st.session_state.get("active_model")
        if model_key:
            if model_key not in st.session_state:
                st.session_state[model_key] = prior or ETF
            model = st.sidebar.selectbox("Decision model", (ETF, CLASSROOM), key=model_key,
                                         format_func=lambda item: "Training and validation" if item == CLASSROOM else item)
            if model == ETF:
                window = st.sidebar.radio("ETF risk window", (36, 60), index=1, format_func=lambda m: f"{m} months")
        else:
            st.sidebar.caption("Training and validation · ETF snapshot unavailable")
            if prior == ETF:
                st.warning("Reviewed ETF data became unavailable. This page now shows Training and validation.")
        st.session_state["active_model"] = model
        with st.sidebar.expander("Committee action under review"):
            requested = st.selectbox("Action to assess", ACTIONS, index=3,
                                     format_func=lambda action: "PILOT · process only" if action == "PILOT" else action)
        custom = st.session_state["scenario_mode"] == "Custom scenario"
        etf_annual_cost = ANNUAL_COST
        if model == ETF and custom:
            panel = st.container() if page == BUILDER and builder_view == "Allocation" else st.sidebar
            with panel:
                etf_annual_cost = st.number_input(
                    "ETF recurring cost (bp)", min_value=0.0, max_value=10000.0,
                    value=ANNUAL_COST * 10000, step=1.0, key="scenario_etf_cost_bp",
                    help="Hypothetical annual investor fee, excluding fund expenses already reflected in the forward assumptions.",
                ) / 10000
        if page == BUILDER and builder_view == RESEARCH:
            st.header(RESEARCH)
            topics = ("Fund comparison", "Historical Market Data", "Economic Signals", "Security Search")
            topic = st.selectbox("Research area", topics, key="research_topic",
                                 format_func=lambda name: "Advanced · Security Search" if name == "Security Search" else name)
            if topic == "Historical Market Data":
                historical_view(data.etf, mandate, reviewed or verified_etf, data.etf_status)
            elif topic == "Economic Signals":
                signal_view(data.archive, signal_date, signal, data.signal_status)
            elif topic == "Security Search":
                security_view(data.etf, reviewed or verified_etf, mandate)
            else:
                research_context = build_context(mandate, model, data.etf, window,
                                                 st.session_state.get(f"custom_mix_{model}") if custom else None,
                                                 etf_annual_cost=etf_annual_cost)
                fund_explorer(mandate, data.etf if model == ETF else None, context=research_context)
            return
        storage = f"custom_mix_{model}"
        context = build_context(mandate, model, data.etf, window, st.session_state.get(storage) if custom else None,
                                etf_annual_cost=etf_annual_cost)
        stress_key = (model, window, mandate, context.active.weights if context.active else None,
                      data.etf.csv_hash if model == ETF else None, custom, context.annual_cost)
        saved_stress = st.session_state.get("reviewed_stress")
        challenge = saved_stress[1] if saved_stress and saved_stress[0] == stress_key else None
        if page not in (DASHBOARD, COMMITTEE):
            st.caption(model_label(context))
        etf_note = None
        if model == CLASSROOM and not verified_etf:
            etf_note = project_etf_finding()
        if page == DASHBOARD:
            dashboard(context, investment_brief(context, signal, requested), model_label(context), custom=custom,
                      model_key=model_key, etf_note=etf_note)
        elif page == BUILDER:
            simulator(context, storage, custom=custom)
            decision = decision_for(context, signal, requested)
            st.caption(f"Feasibility: {decision.feasibility}. Investment disposition: {decision.action}. $0 live.")
            choices = compared(context)
            st.altair_chart(risk_chart(choices, mandate.target), width="stretch")
            show_allocation_comparison(context, choices.portfolios)
            with st.expander("Investment horizon and target value"):
                st.metric(f"Target value in {mandate.horizon} years", f"${mandate.target_value:,.0f}")
                st.caption("Annual compounding without cash flows.")
            show_resilience(context)
        elif page == RISK:
            st.header(RISK)
            topic = st.selectbox("Lab analysis", ("Stress testing", "Risk and allocation comparison",
                                                  "Historical performance", "Economic signal"), key="lab_topic")
            if topic == "Stress testing":
                if model == ETF:
                    challenge = etf_stress_view(context, signal, requested)
                else:
                    show_classroom_overview(context, signal, requested)
                    options = {}
                    if context.active is not None and context.active != context.optimized:
                        options["active"] = context.active
                    if requested != "PILOT":
                        options["requested"] = requested
                    challenge = stress_view(mandate, **options)
                    with st.expander("Separate historical ETF reference"):
                        show_historical(data.etf, reviewed=reviewed or verified_etf)
                if challenge is not None and challenge.label != "Base case":
                    show_stability(context, challenge)
                st.session_state["reviewed_stress"] = (stress_key, challenge)
            elif topic == "Risk and allocation comparison":
                if model == ETF:
                    st.dataframe(portfolio_table(context.windows), hide_index=True)
                    reference = context.active or context.analysis.portfolios[1]
                    vols = [portfolio_metrics(reference.weights, context.gross_returns, w.annual_covariance,
                                              context.annual_cost)[2] for w in context.windows]
                    window_data = pd.DataFrame({"Window": [f"{w.months} months" for w in context.windows],
                                                "Annual volatility": vols})
                    st.altair_chart(alt.Chart(window_data).mark_bar(color=DARK_GOLD).encode(
                        x=alt.X("Annual volatility:Q", axis=alt.Axis(format="%")),
                        y=alt.Y("Window:N", title=None), tooltip=["Window", alt.Tooltip("Annual volatility:Q", format=".2%")]
                    ).properties(height=85), width="stretch")
                    st.caption(f"{reference.name} at fixed weights: {vols[0]:.2%} with 36 months vs "
                               f"{vols[1]:.2%} with 60 months. Forward assumptions and the return ceiling are unchanged.")
                portfolio_analysis(context)
            elif topic == "Historical performance":
                active_history(context)
            else:
                signal_view(data.archive, signal_date, signal, data.signal_status)
        elif page == ANALYST:
            stress_failed = bool(saved_stress and saved_stress[0] == stress_key and challenge is None)
            show_analyst(context, signal, requested, challenge, custom=custom, stress_failed=stress_failed,
                         source_rejected="rejected:" in data.signal_status.lower(), etf_note=etf_note)
        elif page == COMMITTEE:
            topic = st.selectbox("Review area", ("Decision summary", "Mandate and methodology", "Experiment replay",
                                                 "Data sources and tests"), key="validation_topic")
            if topic == "Decision summary":
                brief = investment_brief(context, signal, requested)
                ranges = (weight_ranges(mandate) if model == CLASSROOM and context.active
                          and context.active == context.optimized else ())
                sections = committee_sections(context, signal, requested,
                                              "Custom scenario" if custom else "Lab 13 default client",
                                              challenge, brief, ranges=ranges, etf_note=etf_note)
                committee_briefing(sections, brief)
                reviewed_etf_access(model_key, context)
                summary = committee_summary(sections)
                if model == ETF:
                    st.caption("Private snapshot results. Confirm permission before sharing this summary.")
                st.download_button("Download committee summary", summary, "committee-summary.md")
            elif topic == "Experiment replay":
                if "experiment_upload" in st.session_state:
                    experiment_view()
                else:
                    st.info("No experiment loaded. Optionally import an exported JSON in Advanced Data Management.")
            elif topic == "Data sources and tests":
                st.write(f"**ETF data** · {data.etf_status}")
                st.write(f"**Credit signal** · {data.signal_status}")
                st.caption("Reproduction commands are in README.md. Executed tests are recorded in outputs/validation-summary.md.")
            elif model == ETF:
                st.header("ETF mandate and methodology")
                st.caption("IEF and LQD provisionally count as bonds. BIL provisionally counts as reserve. "
                           "The fund wrappers and five-day liquidity still require review.")
                st.dataframe(portfolio_table(context.windows), hide_index=True)
                st.dataframe(pd.DataFrame([{"Portfolio": p.name, "Rule": r.name, "Status": r.status, "Evidence": r.detail}
                                           for p in compared(context).portfolios for r in p.rules]), hide_index=True)
            else:
                compliance(compared(context))
    except (ValueError, ArithmeticError) as error:
        st.error(f"Analysis unavailable. {error}")


if __name__ == "__main__":
    main()
