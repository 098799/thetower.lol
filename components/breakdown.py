import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.results import compute_results
from dtower.tourney_results.constants import Graph, Options, champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch


def compute_breakdown(df: pd.DataFrame, options: Optional[Options] = None) -> None:
    sus_ids = get_sus_ids()

    def get_data(df):
        non_sus_df = df[~df.id.isin(sus_ids)]
        unique_roles = sorted(non_sus_df.wave_role.unique(), key=lambda role: role.wave_bottom)
        unique_dates = non_sus_df.date.unique()

        counts_per_date = non_sus_df.groupby(["date", "wave_role"])

        date_counts = non_sus_df.groupby("date").count()
        total_per_date = {date: count for date, count in zip(date_counts.index, date_counts.id)}

        counts_data = {role: {date: 0 for date in unique_dates} for role in unique_roles}

        for (date, role), counts in counts_per_date:
            count = counts.count()[0] if not counts.empty else 0
            counts_data[role][date] = count

        return unique_dates, counts_data

    dates, counts_data = get_data(df)

    plot_data = {
        role: go.Bar(
            name=f"{role.wave_bottom} v{role.patch.version_minor}{role.patch.version_patch}{'' if not role.patch.beta else ' beta'}",
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

    glory_patch = Patch.objects.get(version_minor=16)

    plot_data = {
        role: go.Bar(
            name=f"{role.wave_bottom} v{role.patch.version_minor}",
            x=[date for date in dates if date >= glory_patch.start_date and date <= glory_patch.end_date],
            y=[value for date, value in count_data.items() if date >= glory_patch.start_date and date <= glory_patch.end_date],
            marker_color=role.color,
            opacity=0.8,
        )
        for role, count_data in counts_data.items()
        if role.patch.version_minor == glory_patch.version_minor
    }

    fig = go.Figure(data=list(plot_data.values()))
    fig.update_layout(barmode="stack", title="Glory days of 0.16-0.17")

    st.plotly_chart(fig)


# import cProfile
# import pstats

# pr = cProfile.Profile()
# df = load_tourney_results("data")
# pr.run("compute_breakdown(df)")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)

if __name__ == "__main__":
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ], result_cutoff=200)
    compute_breakdown(df, options)
