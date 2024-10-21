import pandas as pd
import streamlit as st

from components.util import deprecated
from dtower.tourney_results.constants import Graph, Options, champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.formatting import make_player_url


def compute_namechangers(df, options=None):
    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    df = df[~df.id.isin(get_sus_ids())]

    combined_data = []

    for id, data in df.groupby("id"):
        if len(data.tourney_name.unique()) == 1:
            continue

        real_name = data.real_name.iloc[0]
        how_many_rows = len(data)
        how_many_names = len(data.tourney_name.unique())
        last_performance = data[-5:].wave.mean()

        combined_data.append(
            {
                "real_name": real_name,
                "id": id,
                "namechanged_times": how_many_names,
                "no_in_champ": how_many_rows,
                "mean_last_5_tourneys": int(round(last_performance, 0)),
            }
        )

    new_df = pd.DataFrame(combined_data)
    new_df = new_df.sort_values("namechanged_times", ascending=False).reset_index(drop=True)

    to_be_displayed = new_df.style.format(make_player_url, subset=["id"])

    st.write(to_be_displayed.to_html(escape=False, index=False), unsafe_allow_html=True)


def get_namechangers():
    deprecated()
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ])
    compute_namechangers(df, options)
