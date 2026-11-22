"""Shared BoilerPortfolio labels and presentation helpers."""

import streamlit as st

DASHBOARD = "Investment Overview"
RESEARCH = "Research and data"
BUILDER = "Portfolio Builder"
PERFORMANCE = "Portfolio Performance"
RISK = "Risk & Scenario Analysis"
ANALYST = "Investment Assistant"
COMMITTEE = "Committee Decision"
PAGES = (DASHBOARD, BUILDER, RISK, COMMITTEE, ANALYST)

INK = "#222222"
GOLD = "#CFB991"
DARK_GOLD = "#8B6D35"
GRAY = "#71716F"
CHART_COLORS = (INK, DARK_GOLD, GRAY, GOLD, "#A09A92")


def metric_cards(values, columns=4):
    for start in range(0, len(values), columns):
        for column, (label, value) in zip(st.columns(columns), values[start:start + columns]):
            column.metric(label, value, border=True)


def next_steps():
    st.subheader("Next steps")
    left, middle, right = st.columns(3)
    left.button("Explore a custom scenario", on_click=go_to, args=(BUILDER,),
                kwargs={"custom": True}, width="stretch")
    middle.button("Test portfolio risk", on_click=go_to, args=(RISK,), width="stretch")
    right.button("Review committee evidence", on_click=go_to, args=(COMMITTEE,), width="stretch")


def go_to(page, *, custom=False):
    st.session_state["page"] = page
    if custom:
        st.session_state["scenario_mode"] = "Custom scenario"
