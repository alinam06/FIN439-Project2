"""Decision-first dashboard and committee presentation."""

import streamlit as st

from src.feasibility_view import return_ceiling_chart
from src.presentation import COMMITTEE, DASHBOARD, metric_cards, next_steps


def _action(brief):
    render = st.warning if brief.action == "REJECT" else st.markdown
    render(f"**{brief.action}** · {brief.ask}")
    st.caption(f"Portfolio feasibility: {brief.feasibility}. Process: {brief.process}")


def dashboard(context, brief, model_label, *, custom=False, model_key=None, etf_note=None):
    st.header(DASHBOARD)
    investor = "Custom scenario" if custom else "Lab 13 default client"
    mandate, active = context.mandate, context.active
    value = mandate.portfolio_value
    compact = f"${value / 1e6:g}M" if value >= 1e6 else f"${value:,.0f}"
    st.caption(f"{investor} · {model_label} · {compact} · {mandate.horizon} years")
    _action(brief)
    ceiling = context.analysis.max_net_return
    metric_cards((
        ("Net target", f"{mandate.target:.2%}"),
        ("Net ceiling", f"{ceiling:.2%}" if ceiling is not None else "Unavailable"),
        ("Margin", f"{(ceiling - mandate.target)*10000:+.0f} bp" if ceiling is not None else "Unavailable"),
        ("Live capital", f"${brief.capital:,.0f}"),
    ))
    if ceiling is not None:
        st.altair_chart(return_ceiling_chart([("Net ceiling", ceiling)], mandate.target), width="stretch")
    if active:
        st.caption(f"Active mix: {active.net_return:.2%} expected net · {active.volatility:.2%} annual volatility · "
                   f"Mandate {active.verdict}.")
    st.markdown(f"**Approval gate:** {brief.approval_gap}")
    if etf_note:
        with st.expander("Previously documented ETF decision"):
            st.markdown(etf_note)
    reviewed_etf_access(model_key, context)
    if ceiling is not None and ceiling < mandate.target:
        advice = ("Validate BIL, IEF, LQD and VT return assumptions and screen mandate-eligible alternatives."
                  if context.windows else "Compare the existing benchmark and modeled constraints in Portfolio Builder.")
        st.write(f"Keep live capital at zero. {advice} The saved Lab 13 mandate stays fixed.")
    elif ceiling is None:
        st.write("Keep live capital at zero. Check whether the modeled bond and reserve floors can be met together.")
    elif active and active.verdict == "Fail":
        st.write("Withhold the current allocation. Review its failed rules in Portfolio Builder. "
                 "The saved Lab 13 mandate stays fixed.")
    next_steps()


def reviewed_etf_access(model_key, context):
    if context.sample is not None:
        return
    if model_key:
        st.button("Open reviewed ETF analysis", on_click=st.session_state.update,
                  args=({model_key: "Reviewed ETF snapshot"},))
    else:
        st.caption("Reviewed ETF analysis requires an authorized local snapshot. "
                   "The public default runs without private data or API credentials.")


def committee_briefing(sections, brief):
    st.header(COMMITTEE)
    heading, body = sections[0]
    st.subheader(heading)
    display = st.warning if brief.action == "REJECT" else st.markdown
    display(body)
    st.caption("Proposed live allocation range: 0%–0%.")
    for heading, body in sections[1:]:
        if heading in ("Portfolio comparison", "Monitoring and approval conditions"):
            with st.expander(heading):
                st.markdown(body)
        elif heading in ("Investment rationale", "Main financial risks", "Stress-test conclusions"):
            st.markdown(f"**{heading}**")
            st.markdown(body)
        elif heading == "Proposed committee actions":
            gate = brief.approval_gap
            if brief.action == "REJECT":
                gate += " Reassess only when a candidate meets the net objective and modeled allocation limits."
            st.markdown(f"**Approval gates** · {gate}")
