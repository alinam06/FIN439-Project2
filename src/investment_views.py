"""Allocation, fund research and decision explanation views."""

from dataclasses import replace

import altair as alt
import pandas as pd
import streamlit as st

from src.assumptions import ASSETS, CORRELATIONS
from src.committee import decision_for
from src.etf_decision_view import decision_case
from src.etf_portfolio import analyze_windows, downside_returns, snapshot_date
from src.briefing import DATED_CREDIT_EVIDENCE, exclusion_effect, model_scope, monitoring_rows
from src.judgment import attribution, restrictions
from src.historical import TICKERS
from src.investment_context import ETF, entered_weights
from src.presentation import CHART_COLORS, metric_cards
from src.security_research import PROFILES, historical_metrics, mandate_notes
from src.stress import assess_stress, preset


def set_mix(storage, weights):
    if weights is None:
        st.session_state.pop(storage, None)
    else:
        st.session_state[storage] = tuple(weights)
    st.session_state.weight_editor_revision = st.session_state.get("weight_editor_revision", 0) + 1


def simulator(context, storage, *, custom):
    active = context.active
    if not custom:
        st.caption("Choose Custom scenario above to edit weights without changing the Lab 13 mandate.")
    else:
        left, right = st.columns(2)
        left.button("Use constrained optimum", disabled=context.optimized is None,
                    on_click=set_mix, args=(storage, None), width="stretch")
        right.button("Load equal weights", on_click=set_mix,
                     args=(storage, context.analysis.portfolios[0].weights), width="stretch")
        if context.optimized is None:
            st.caption("No constrained optimum is available for the current target and limits.")
        default = active or context.analysis.portfolios[0]
        percentages = [round(100 * weight, 6) for weight in default.weights]
        largest = percentages.index(max(percentages))
        percentages[largest] = round(percentages[largest] + 100 - sum(percentages), 6)
        revision = st.session_state.get("weight_editor_revision", 0)
        with st.form(f"allocation_{storage}_{revision}"):
            cols = st.columns(len(context.asset_names))
            entries = [column.number_input(name, 0.0, 100.0, value, .25, format="%.6f", key=f"{storage}_{revision}_{i}",
                                          help="Percentage of portfolio")
                       for i, (column, name, value) in enumerate(zip(cols, context.asset_names, percentages))]
            submitted = st.form_submit_button("Apply allocation")
        if submitted:
            try:
                set_mix(storage, entered_weights(entries))
            except ValueError as error:
                st.error(str(error))
            else:
                st.rerun()
    if active:
        bonds, reserve = context.exposure(active.weights)
        metric_cards((("Net annual return", f"{active.net_return:.2%}"),
                      ("Annual volatility", f"{active.volatility:.2%}"),
                      ("Target margin", f"{(active.net_return - context.mandate.target) * 1e4:+.1f} bp"),
                      ("Mandate", active.verdict)))
        st.caption(f"Recurring cost {context.annual_cost:.2%} · IG bonds {bonds:.2%} · Reserve {reserve:.2%}")
        checks_panel((active,))
    if active is None:
        st.warning(context.analysis.decision)


def checks_panel(portfolios):
    with st.expander("Individual mandate checks"):
        st.dataframe(pd.DataFrame([
            {"Portfolio": p.name, "Rule": rule.name, "Status": rule.status, "Evidence": rule.detail}
            for p in portfolios for rule in p.rules
        ]), hide_index=True)


def line_chart(frame, title, format):
    series = frame.rename_axis("Date").reset_index().melt("Date", var_name="Investment", value_name="Value")
    st.altair_chart(alt.Chart(series).mark_line().encode(
        x=alt.X("Date:T", title="Monthly observation date"),
        y=alt.Y("Value:Q", title=title, axis=alt.Axis(format=format), scale=alt.Scale(zero=False)),
        color=alt.Color("Investment:N", scale=alt.Scale(range=list(CHART_COLORS))),
        tooltip=["Date:T", "Investment:N", alt.Tooltip("Value:Q", format=format)],
    ).properties(height=245).interactive(), width="stretch")


def heatmap(correlation):
    cells = correlation.rename_axis("Investment").reset_index().melt("Investment", var_name="Comparison",
                                                                      value_name="Correlation")
    base = alt.Chart(cells).encode(x="Investment:N", y="Comparison:N")
    marks = base.mark_rect().encode(color=alt.Color("Correlation:Q", scale=alt.Scale(
        domain=[-1, 0, 1], range=["#828482", "#ffffff", "#CFB991"])),
        tooltip=["Investment:N", "Comparison:N", alt.Tooltip("Correlation:Q", format=".2f")])
    st.altair_chart(marks + base.mark_text(color="#222222").encode(
        text=alt.Text("Correlation:Q", format=".2f")), width="stretch")


def fund_explorer(mandate, sample, *, context=None):
    st.write("Compare the four ETF candidates and their potential roles in the mandate.")
    selected = st.multiselect("Funds to compare", TICKERS, default=list(TICKERS))
    if not selected:
        st.info("Select at least one fund to compare.")
        return
    for ticker in selected:
        profile = PROFILES[ticker]
        with st.expander(f"{ticker} · {profile.name}", expanded=len(selected) == 1):
            st.write(f"**Objective / category** · {profile.category}  ")
            st.write(f"**Portfolio role** · {profile.role}. {profile.characteristic}")
            st.write(f"**Eligibility unverified** · {mandate_notes(profile, mandate)}")
            st.link_button("Issuer fund profile", profile.source)
    if context is not None:
        with st.expander("Portfolio sleeve research", expanded=True):
            stats = (attribution(context.active.weights, context.gross_returns, context.risk, context.annual_cost)
                     if context.active else None)
            roles = ("Liquid reserve", "Treasury duration / bond floor", "IG credit / bond floor",
                     "Global growth / equity risk", "Company growth / issuer concentration")
            items = []
            for i, name in enumerate(context.asset_names):
                exclusion = exclusion_effect(context, i)
                items.append({
                    "Active sleeve": name, "Modeled role": roles[i],
                    "Gross return assumption": f"{context.gross_returns[i]:.2%}",
                    "Standalone annual volatility": f"{context.risk[i,i]**.5:.2%}",
                    "Gross contribution": f"{stats.gross_by_asset[i]:.2%}" if stats else "Unavailable",
                    "Risk contribution": f"{stats.risk_by_asset[i]:+.2%}" if stats and stats.risk_by_asset is not None else "Unavailable",
                    "Without sleeve · pro rata": (
                        f"{(exclusion.net_return-context.active.net_return)*100:+.2f} pp net, "
                        f"{(exclusion.volatility-context.active.volatility)*100:+.2f} pp volatility · {exclusion.verdict}"
                        if exclusion else "Unavailable or weight already zero"),
                })
            st.dataframe(pd.DataFrame(items), hide_index=True, width="stretch")
            st.caption("Exclusion redistributes weight across the remaining active holdings proportionally. "
                       "It is a diagnostic under the active model, with no reoptimization or trades.")
    if sample is None:
        st.info("Historical fund statistics are unavailable without a locally reviewed ETF snapshot.")
        st.caption("Illustrative sleeve assumptions from Lab 14. These values describe model exposures.")
        indices = [TICKERS.index(ticker) for ticker in selected]
        st.dataframe(pd.DataFrame([
            {"ETF candidate": TICKERS[i], "Classroom sleeve": ASSETS[i].name,
             "Illustrative gross return": f"{ASSETS[i].gross_return:.2%}",
             "Illustrative volatility": f"{ASSETS[i].volatility:.2%}"} for i in indices
        ]), hide_index=True)
        heatmap(pd.DataFrame(CORRELATIONS, index=(*TICKERS, "Classroom stock"),
                             columns=(*TICKERS, "Classroom stock")).loc[selected, selected])
        st.caption("Classroom sleeve correlations labeled by the related ETF candidates.")
        return
    months = st.radio("Historical comparison window", (36, 60), index=1, horizontal=True)
    prices = sample.prices.loc[:, selected].tail(months + 1)
    st.caption(f"Private Alpha Vantage monthly adjusted closes · USD · {prices.index[0].date()} to "
               f"{prices.index[-1].date()} · captured {snapshot_date(sample)}.")
    growth, drawdown, metrics, correlation = historical_metrics(prices)
    st.dataframe(metrics.style.format("{:.2%}"))
    line_chart(prices, "Monthly distribution-adjusted close (USD)", "$.2f")
    line_chart(growth, "Growth of $100 · distributions reflected", "$.2f")
    line_chart(drawdown, "Drawdown from prior monthly peak", ".1%")
    if len(selected) > 1:
        heatmap(correlation)


def active_history(context):
    st.subheader("Historical portfolio performance")
    if context.model != ETF or context.active is None:
        st.info("Portfolio history requires a reviewed ETF allocation. Classroom sleeves use forward assumptions.")
        return
    returns = context.sample.returns.tail(context.window)
    weighted = returns @ context.active.weights
    initial = context.sample.prices.index[-context.window - 1]
    growth = pd.concat([pd.Series([1.0], index=[initial]), (1 + weighted).cumprod()])
    st.caption(f"{initial.date()} to {returns.index[-1].date()} · USD adjusted-price returns · fixed weights "
               "rebalanced monthly in this retrospective illustration, before fees, taxes, and trade costs.")
    line_chart((growth * 10_000).to_frame(context.active.name), "Growth of $10,000", "$,.0f")
    line_chart((growth - 1).to_frame(context.active.name), "Cumulative historical return", ".1%")
    line_chart((growth / growth.cummax() - 1).to_frame(context.active.name), "Monthly drawdown", ".1%")
    heatmap(returns.corr())


def stress_summary(context, label, analysis, held, signal, requested):
    action = decision_for(context, signal, requested, analysis=analysis).action
    ceiling = "unavailable" if analysis.max_net_return is None else f"{analysis.max_net_return:.2%}"
    held_text = (f"Holding the same weights gives {held.net_return:.2%} net and "
                 f"{held.volatility:.2%} volatility ({held.verdict})." if held else "There are no active weights to hold.")
    return f"{label}. The modeled ceiling is {ceiling}. {held_text} Reoptimizing leads to {action}."


def adverse_summary(context, signal, requested, challenge=None):
    if challenge is not None:
        return stress_summary(context, challenge.label, challenge.analysis, challenge.held, signal, requested)
    if context.model == ETF:
        gross = downside_returns(context.gross_returns, .01)
        windows = analyze_windows(context.sample, context.mandate, snapshot_date(context.sample),
                                  gross, context.annual_cost, reviewed=True)
        window = windows[0 if context.window == 36 else 1]
        analysis = decision_case(window, context.mandate)
        held = (replace(context, gross_returns=gross).evaluate(context.active.weights)
                if context.active else None)
        label = "LQD and VT expected returns fall 1 percentage point"
    else:
        inputs, stressed = preset("Equity market deterioration", context.mandate)
        stress = assess_stress(context.mandate, stressed, inputs, active=context.active)
        analysis, held = stress.stressed, stress.held
        label = "equity expected returns fall 2 percentage points and equity volatility rises 25%"
    return stress_summary(context, f"Standard sensitivity: {label}", analysis, held, signal, requested)


def binding_checks(context):
    return tuple(check.name for check in restrictions(context) if check.status == "At limit")


def committee_sections(context, signal, requested, investor, challenge, brief, *, ranges=(), etf_note=None):
    """One briefing rendered in the app and exported as Markdown."""
    mandate, active = context.mandate, context.active
    ceiling = context.analysis.max_net_return
    title = (f"{investor} · ${mandate.portfolio_value:,.0f} · {mandate.horizon} years"
             + (f" · {context.window}-month risk window · captured {snapshot_date(context.sample)}"
                if context.model == ETF else ""))
    recommendation_text = (f"**{brief.action}** · {brief.ask} **Live capital authorization: "
                           f"${brief.capital:,.0f}.**")
    if context.model == ETF and brief.action == "REJECT":
        recommendation_text = ("**REJECT** the ETF allocation under the active assumptions. "
                               "**Live capital authorization: $0.**")
    recommendation_text += f" Portfolio feasibility: **{brief.feasibility}**. Process: {brief.process}"
    rationale = ([etf_note] if etf_note else []) + [title, model_scope(context),
                 f"Annual net objective: **{mandate.target:.2%}**."
                 + (f" Modeled ceiling: **{ceiling:.2%}** ({(ceiling-mandate.target)*10000:+.0f} bp vs objective)."
                    if ceiling is not None else " No modeled weight set meets the allocation limits.")]
    if active is None and ceiling is not None:
        rationale.append("No target-meeting candidate under the active assumptions.")
    if context.model == ETF and ceiling is not None and ceiling < mandate.target:
        rationale.append("Under the modeled reserve and bond floors and recurring cost, the forward return assumptions "
                         "leave a shortfall. Changing the covariance window cannot raise the return ceiling. "
                         "Reconsider only after defensible new return or cost evidence, or a separately approved "
                         "universe or mandate change, supports a robust, suitable candidate.")
    compared = context.analysis.portfolios
    if active and active not in compared:
        compared += (active,)
    comparisons = ["| Portfolio | Expected net return | Annual volatility | Current assessment |",
                   "| --- | ---: | ---: | --- |"]
    for portfolio in compared:
        failed = ", ".join(rule.name for rule in portfolio.rules if rule.status == "Fail")
        verdict = f"Modeled failures: {failed}" if failed else (
            "Modeled checks met. Evidence pending." if portfolio.verdict == "Unverified" else portfolio.verdict)
        comparisons.append(f"| {portfolio.name} | {portfolio.net_return:.2%} | {portfolio.volatility:.2%} | {verdict} |")
    if context.optimized is None:
        comparisons.append("| Constrained portfolio | — | — | No feasible solution |")
    if active:
        weights = ", ".join(f"{asset} {weight:.2%}" for asset, weight in zip(context.asset_names, active.weights))
        comparisons += ["", f"**{active.name} weights:** {weights}."]
    if ranges:
        comparisons += ["", "| Illustrative sleeve | Min | Max |", "| --- | ---: | ---: |",
                        *(f"| {asset} | {low:.2%} | {high:.2%} |"
                          for asset, (low, high) in zip(context.asset_names, ranges))]
    risks = [f"{finding.evidence} {finding.implication}" for finding in brief.findings
             if finding.question == "Where is the risk concentrated?"]
    if not risks and not context.windows:
        benchmark = context.analysis.portfolios[1]
        risks = [f"The benchmark has {benchmark.volatility:.2%} modeled annual volatility. "
                 "Active-portfolio attribution is unavailable."]
    if context.windows:
        risks.append("Benchmark volatility at fixed weights was " + " and ".join(
            f"{window.portfolios['60% VT / 40% LQD'].volatility:.2%} over {window.months} months"
            for window in context.windows) + ".")
    risks.append("Annual loss tolerance is unresolved. Volatility measures variability.")
    selected = challenge if challenge and challenge.label != "Base case" else None
    stress = adverse_summary(context, signal, requested, selected)
    actions = [f"- **{name}** · {detail}" for name, detail in brief.register if name != "Process"]
    if active is None or active.verdict == "Fail":
        actions.append("- Reassess only when a candidate meets the net objective and modeled allocation limits.")
    monitoring = ["| Monitor | Current status | Threshold or approval condition | Response if breached or missing |",
                  "| --- | --- | --- | --- |"]
    for _, name, current, threshold, _, response in monitoring_rows(context, signal):
        monitoring.append(f"| {name} | {current} | {threshold} | {response} |")
    if signal is None or signal.status == "Unavailable":
        signal_note = "Live BAA10Y is unavailable."
    else:
        latest = f" Latest eligible observation: {signal.history[-1].observation_date}." if signal.history else ""
        signal_note = f"Live BAA10Y is unavailable. Authorized archive, date-level assessment: {signal.status}.{latest}"
    monitoring += ["", signal_note + " " + DATED_CREDIT_EVIDENCE + " The signal leaves weights fixed.",
                   "Break-even thresholds are analytical. Live implementation requires a separate committee vote."]
    return (
        ("Executive recommendation", recommendation_text),
        ("Investment rationale", "\n\n".join(rationale)),
        ("Portfolio comparison", "\n".join(comparisons)),
        ("Main financial risks", "\n\n".join(risks)),
        ("Stress-test conclusions", stress),
        ("Proposed committee actions", "\n".join(actions)),
        ("Monitoring and approval conditions", "\n".join(monitoring)),
    )


def committee_summary(sections):
    return "# BoilerPortfolio committee briefing\n\n" + "\n\n".join(
        f"## {heading}\n\n{body}" for heading, body in sections
    ) + "\n"
