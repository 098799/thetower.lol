import pandas as pd
import streamlit as st

from components.player_lookup import compute_player_lookup
from dtower.tourney_results.constants import Graph, Options, league_to_folder
from dtower.tourney_results.data import load_tourney_results

compute_search_all_leagues = compute_player_lookup

if __name__ == "__main__":
    my_bar = st.progress(0)
    leagues = sorted(league_to_folder.items())

    dfs = []

    for index, (_, league) in enumerate(leagues, 1):
        df = load_tourney_results(league)
        my_bar.progress(index / len(leagues))

        dfs.append(df)

    for df, (league, _) in zip(dfs, leagues):
        df["league"] = league

    df = pd.concat(dfs)
    my_bar.empty()

    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)

    compute_search_all_leagues(df, options)
