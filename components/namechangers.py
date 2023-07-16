import pandas as pd
import streamlit as st

from dtower.tourney_results.constants import Graph, Options, champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results


def compute_namechangers(df, options=None):
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
                "no_in_champ": how_many_rows,
                "namechanged_times": how_many_names,
                "mean_last_5_tourneys": int(round(last_performance, 0)),
            }
        )

    new_df = pd.DataFrame(combined_data)
    new_df = new_df.sort_values("namechanged_times", ascending=False).reset_index(drop=True)

    to_be_displayed = new_df.style.apply(lambda row: [f"color: {df[df.real_name == row.real_name].iloc[-1].name_role_color}", None, None, None], axis=1)

    st.dataframe(to_be_displayed, use_container_width=True, height=800)


if __name__ == "__main__":
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ])
    compute_namechangers(df, options)
