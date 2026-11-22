"""Native Streamlit chat for the local Investment Analyst."""

import streamlit as st

from src.analyst import answer_question, suggested_questions
from src.committee import decision_for
from src.presentation import ANALYST

HISTORY = "analyst_history"


def show_analyst(context, signal, requested, challenge, *, custom, stress_failed=False, source_rejected=False, etf_note=None):
    st.header(ANALYST)
    st.caption("Deterministic portfolio explanations · Runs offline")
    left, right = st.columns((3, 1))
    active = context.active
    investor = "Custom scenario" if custom else "Lab 13 default client"
    label = (f"{investor} · ${context.mandate.portfolio_value:,.0f} · "
             f"{context.mandate.target:.2%} net target · {active.name if active else 'No active mix'}")
    left.caption(label)
    history = st.session_state.setdefault(HISTORY, [])
    signal_stamp = (signal.status, signal.change_pp, signal.explanation, signal.history[-1:]
                    ) if signal is not None else None
    stamp = (context.model, context.window, context.mandate, context.annual_cost, active, custom, signal_stamp, source_rejected, etf_note,
             requested, challenge, stress_failed, context.sample.csv_hash if context.sample is not None else None)

    suggestion = None
    st.caption("Suggested questions")
    questions = suggested_questions(context)
    for column, question in zip(st.columns(3), questions[:3]):
        if column.button(question, width="stretch"):
            suggestion = question
    with st.expander("More questions"):
        for question in questions[3:]:
            if st.button(question):
                suggestion = question
    submitted = st.chat_input("Ask about the active decision", max_chars=500)
    question = (submitted or suggestion or "").strip()
    if question:
        response = answer_question(question, context, signal, requested, challenge, stress_failed=stress_failed,
                                   source_rejected=source_rejected, etf_note=etf_note)
        action = decision_for(context, signal, requested).action
        history.append((question, response, f"{label} · {context.model} · {action}", stamp))

    right.button("Clear conversation", disabled=not history, on_click=st.session_state.pop,
                 args=(HISTORY, None))
    for prompt, response, saved_label, saved_stamp in history:
        with st.chat_message("user"):
            st.text(prompt)
        with st.chat_message("assistant"):
            if saved_stamp != stamp:
                st.caption("Earlier scenario or inputs · " + saved_label)
            st.markdown(response)
