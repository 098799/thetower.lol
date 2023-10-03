import datetime
import os
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.results import compute_results
from dtower.tourney_results.constants import Graph, Options, champ, league_to_folder
from dtower.tourney_results.data import get_patches, get_sus_ids, load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch
from dtower.tourney_results.models import TourneyResult

patches = sorted(
    [patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True
)


def compute_breakdown(df: pd.DataFrame, options: Optional[Options] = None) -> None:
    sus_ids = get_sus_ids()
    hidden_features = os.environ.get("HIDDEN_FEATURES")

    def get_data(df, role_type="wave_role", overfill=200):
        non_sus_df = df[~df.id.isin(sus_ids)]
        unique_roles = sorted(non_sus_df[role_type].unique(), key=lambda role: role.wave_bottom)
        unique_dates = non_sus_df.date.unique()

        counts_per_date = non_sus_df.groupby(["date", role_type])

        date_counts = non_sus_df.groupby("date").count()
        total_per_date = {date: count for date, count in zip(date_counts.index, date_counts.id)}
        overfill_per_date = {date: max(overfill - count, 0) for date, count in total_per_date.items()}

        counts_data = {role: {date: 0 for date in unique_dates} for role in unique_roles}

        for (date, role), counts in counts_per_date:
            count = counts.count()[0] if not counts.empty else 0
            counts_data[role][date] = count

        for date, overfill in overfill_per_date.items():
            counts_data[unique_roles[0]][date] += overfill

        return unique_dates, counts_data

    patches_col, overfill_col = st.columns([3, 1])

    selected_patches = patches_col.multiselect("Limit results to a patch?", patches, default=patches)

    overfill = overfill_col.slider(
        "Overfill results to ", min_value=200, max_value=500 if not hidden_features else 2000, value=200, step=100
    )
    df = load_tourney_results(league_to_folder[champ], result_cutoff=overfill)

    df = df[df.patch.isin(selected_patches)]

    dates, counts_data = get_data(df, overfill=df.groupby("date").id.count().max())
    bcs = {
        date: " / ".join(
            TourneyResult.objects.get(date=date, league=champ).conditions.all().values_list("shortcut", flat=True)
        )
        for date in dates
    }

    plot_data = {
        role: go.Bar(
            name=f"{role.wave_bottom} v{role.patch.version_minor}.{role.patch.version_patch}{'' if not role.patch.interim else ' interim'}",
            x=dates,
            y=list(count_data.values()),
            marker_color=role.color,
            opacity=0.8,
        )
        for role, count_data in counts_data.items()
    }

    fig = go.Figure(data=list(plot_data.values()))
    fig.update_layout(barmode="stack", title="Role counts per tournament (non-sus), courtesy of ObsUK")

    for trace in fig.data:
        trace.customdata = [bcs[date] for date in trace["x"]]
        trace.hovertemplate = "%{x}, %{y}, %{customdata}"

    st.plotly_chart(fig)

    df = load_tourney_results(league_to_folder[champ])

    st.subheader("Scores in each patch")

    patch_breakdown_data = {}

    for patch in selected_patches:
        non_sus_df = df[~df.id.isin(sus_ids)]
        patch_breakdown_datum = {
            patch.wave_bottom: len(players)
            for patch, players in dict(
                non_sus_df[non_sus_df.patch == patch].groupby("name_role").real_name.unique()
            ).items()
        }
        patch_breakdown_data[patch] = patch_breakdown_datum

    all_waves = sorted({wave for patch_data in patch_breakdown_data.values() for wave in patch_data.keys()})

    for patch_data in patch_breakdown_data.values():
        for wave in all_waves:
            patch_data.setdefault(wave, 0)

    data_df = pd.DataFrame(patch_breakdown_data).T.sort_index(axis=1, ascending=False)

    st.dataframe(data_df)

    st.subheader("Scores in each tournament")

    patch_tabs = st.tabs([str(patch) for patch in selected_patches])

    for patch, patch_tab in zip(selected_patches, patch_tabs):
        dates, counts_data = get_data(df[df.patch == patch])
        counts_df = pd.DataFrame({role.wave_bottom: count_data for role, count_data in counts_data.items()})
        patch_tab.dataframe(counts_df.sort_index(axis=1, ascending=False))

    # glory_patch = Patch.objects.get(version_minor=16)

    # plot_data = {
    #     role: go.Bar(
    #         name=f"{role.wave_bottom} v{role.patch.version_minor}",
    #         x=[date for date in dates if date >= glory_patch.start_date and date <= glory_patch.end_date],
    #         y=[value for date, value in count_data.items() if date >= glory_patch.start_date and date <= glory_patch.end_date],
    #         marker_color=role.color,
    #         opacity=0.8,
    #     )
    #     for role, count_data in counts_data.items()
    #     if role.patch.version_minor == glory_patch.version_minor
    # }

    # fig = go.Figure(data=list(plot_data.values()))
    # fig.update_layout(barmode="stack", title="Glory days of 0.16-0.17")

    # st.plotly_chart(fig)


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
    # df = load_tourney_results(league_to_folder[champ], result_cutoff=200)
    compute_breakdown(None, options)
