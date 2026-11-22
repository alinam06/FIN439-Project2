"""Shared chart for showing modeled return ceilings against a requirement."""

import altair as alt
import pandas as pd

from src.presentation import DARK_GOLD, INK


def return_ceiling_chart(rows, target):
    frame = pd.DataFrame(rows, columns=["Case", "Net return"])
    x = alt.X("Net return:Q", title="Annual net return", axis=alt.Axis(format=".1%", tickCount=4),
              scale=alt.Scale(zero=True))
    bars = alt.Chart(frame.dropna(subset=["Net return"])).mark_bar(color=DARK_GOLD, size=20).encode(
        x=x, y=alt.Y("Case:N", sort=frame["Case"].tolist(), title=None,
                     scale=alt.Scale(domain=frame["Case"].tolist()),
                     axis=alt.Axis(labelLimit=140, labelPadding=8, ticks=False)),
        tooltip=["Case", alt.Tooltip("Net return:Q", format=".2%")],
    )
    marker = alt.Chart(pd.DataFrame({"Net return": [target]})).mark_rule(
        color=INK, strokeWidth=2, strokeDash=[5, 3]
    ).encode(x=x, tooltip=[alt.Tooltip("Net return:Q", title="Required net return", format=".2%")])
    return (bars + marker).properties(
        height=max(76, 34 * len(frame)),
        title=alt.Title("Modeled return ceiling", anchor="start",
                        subtitle=f"Dashed line · Required net return {target:.2%}"),
    )
