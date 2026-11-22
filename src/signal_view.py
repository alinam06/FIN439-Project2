"""Economic Signals view. The allocation engine has no dependency on this view."""

import json

import altair as alt
import pandas as pd
import streamlit as st

from src.economic_signal import LOOKBACK
from src.judgment import signal_admission


def signal_view(archive, day, result, status):
    st.subheader("Economic Signals")
    st.subheader("BAA10Y · U.S. corporate credit spread")
    st.caption("Moody’s seasoned Baa yield less the 10-year U.S. Treasury constant-maturity yield. "
               "Daily, percentage points, not seasonally adjusted.")
    st.markdown("[FRED series definition](https://fred.stlouisfed.org/series/BAA10Y) · "
                "[ALFRED vintage archive](https://alfred.stlouisfed.org/series?seid=BAA10Y)")
    st.caption("ALFRED real-time dates are inclusive. Exact source publication times are unverified. "
               "Use this view for date-level review after the day's releases.")
    st.write("Portfolio effect: The signal can prompt a risk review or halt reliance on the signal. "
             "Allocation weights, expected returns, and client constraints stay fixed.")
    disposition, rationale = signal_admission(result, source_rejected="rejected:" in status.lower())
    st.write(f"**{disposition}** · {rationale}")
    if archive is None:
        st.warning(f"Signal unavailable. {status}")
        return
    st.write(f"Selected decision date **{day}**")
    st.caption("Data quality: archive structure and file hash validated. Source attribution is supplied by the uploader.")
    st.write(f"Archive interval {archive.start} to {archive.end} · Retrieved {archive.retrieved_at.isoformat()}")
    st.caption(f"Response SHA-256 {archive.fingerprint}")
    if result.status == "Unavailable":
        st.warning(f"Signal unavailable. {result.explanation} Pause any signal-based decision.")
    else:
        st.info(f"{result.status}. {result.explanation}")
        st.metric("Change over 20 eligible observations", f"{result.change_pp * 100:+.1f} bp")
        st.write(f"Comparison observation {result.history[-1 - LOOKBACK].observation_date}. "
                 "Use the result to review LQD credit and VT equity downside before evaluating a change.")
    st.caption(f"{len(result.history)} eligible numeric observations · "
               f"{result.missing_count} eligible missing values excluded")
    if result.history:
        latest = result.history[-1]
        st.metric("Latest eligible spread", f"{latest.value:.2f} percentage points")
        st.write(f"Observed {latest.observation_date} · ALFRED vintage interval "
                 f"{latest.vintage_start} to {latest.vintage_end} · Publication date and time unverified")
        history = pd.DataFrame({"Observation date": [row.observation_date for row in result.history],
                                "Spread (pp)": [row.value for row in result.history]})
        st.altair_chart(alt.Chart(history).mark_line(point=True).encode(
            x="Observation date:T", y="Spread (pp):Q",
            tooltip=[alt.Tooltip("Observation date:T", format="%Y-%m-%d"),
                     alt.Tooltip("Spread (pp):Q", format=".2f")],
        ).properties(height=280).interactive())
    st.caption("The chart shows the eligible vintage for each observation as of the selected date.")

    evidence = {"decision_date": day, "archive_sha256": archive.fingerprint,
                "retrieved_at": archive.retrieved_at, "status": result.status, "change_pp": result.change_pp,
                "eligible_count": len(result.history), "eligible_missing_count": result.missing_count,
                "latest_observation_date": result.history[-1].observation_date if result.history else None,
                "comparison_observation_date": (result.history[-1 - LOOKBACK].observation_date
                                                 if result.change_pp is not None else None),
                "decision_effect": result.explanation}
    st.download_button("Export signal decision evidence", json.dumps(evidence, default=str, indent=2),
                       "baa10y-decision-evidence.json", mime="application/json")
