from collections import defaultdict
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.constants import Options
from components.data import get_sus_ids, load_tourney_results


def compute_breakdown(df: pd.DataFrame, options: Optional[Options] = None) -> None:
    sus_ids = get_sus_ids()

    def get_data(df):
        non_sus_df = df[~df.id.isin(sus_ids)]
        unique_roles = sorted(non_sus_df.wave_role.unique(), key=lambda role: role.wave_bottom)
        unique_dates = non_sus_df.date.unique()

        counts_data = {role: {date: 0 for date in unique_dates} for role in unique_roles}

        counts_per_date = non_sus_df.groupby(["date", "wave_role"])

        for (date, role), counts in counts_per_date:
            count = counts.count()[0] if not counts.empty else 0
            counts_data[role][date] = count

        return unique_dates, counts_data

    dates, counts_data = get_data(df)

    plot_data = {
        role: go.Bar(
            name=f"{role.wave_bottom} v{role.patch.version_minor}",
            x=dates,
            y=list(count_data.values()),
            marker_color=role.color,
            opacity=0.8,
        )
        for role, count_data in counts_data.items()
    }

    fig = go.Figure(data=list(plot_data.values()))
    fig.update_layout(barmode="stack", title="Role counts per tournament (non-sus), courtesy of ObsUK")

    st.plotly_chart(fig)


# import cProfile
# import pstats

# pr = cProfile.Profile()
# df = load_tourney_results("data")
# pr.run("compute_breakdown(df)")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
