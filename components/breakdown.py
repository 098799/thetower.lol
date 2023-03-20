from collections import defaultdict
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.constants import Options, sus_ids


def compute_breakdown(df: pd.DataFrame, options: Optional[Options] = None) -> None:
    non_sus_df = df[~df.id.isin(sus_ids)]

    counts_per_date = {}

    for date in non_sus_df.date.unique():
        date_df = non_sus_df[non_sus_df["date"] == date]
        counts = date_df.groupby("wave_role").count()

        counts_per_date[date] = counts

    dates = []
    counts_data = defaultdict(list)

    for date, counts in counts_per_date.items():
        dates.append(date)

        for role in sorted(non_sus_df.wave_role.unique(), key=lambda role: role.wave_bottom):
            count_data = counts[counts.index == role]

            if count_data.empty:
                count = 0
            else:
                count = count_data.id.iloc[0]

            counts_data[role].append(count)

    plot_data = {
        role: go.Bar(
            name=f"{role.wave_bottom} v{role.patch.version_minor}",
            x=dates,
            y=count,
        )
        for role, count in counts_data.items()
    }

    for role, datum in plot_data.items():
        datum.update(marker_color=role.color)

    fig = go.Figure(data=list(plot_data.values()))
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode="stack", title="Role counts per tournament (non-sus), courtesy of ObsUK")

    st.plotly_chart(fig)
