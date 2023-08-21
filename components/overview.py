from functools import partial

import pandas as pd
import streamlit as st

from components.results import Results
from dtower.tourney_results.constants import Graph, Options, league_to_folder, leagues
from dtower.tourney_results.data import load_tourney_results
from dtower.tourney_results.formatting import make_url


def compute_overview(dfs, options: Options):
    overall_df = pd.concat(dfs)
    last_tourney = sorted(overall_df.date.unique())[-1]

    with open("style.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    with open("funny.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    for df, league in zip(dfs, leagues):
        st.header(league)

        filtered_df = df[df.date == last_tourney]
        filtered_df = filtered_df.reset_index(drop=True)

        if filtered_df.empty:
            continue

        results = Results(filtered_df, options)
        to_be_displayed = results.prepare_data(filtered_df, how_many=10)
        to_be_displayed_styler = results.regular_preparation(to_be_displayed, filtered_df)
        st.write(
            to_be_displayed_styler.format(partial(make_url, base_url="thetower.lol/Player%20Lookup"), subset=["real_name"])
            .hide(axis="index")
            .to_html(escape=False),
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    df = [load_tourney_results(league, result_cutoff=20) for league in league_to_folder.values()]
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    compute_overview(df, options)
