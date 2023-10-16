import glob
from collections import Counter

import pandas as pd
import streamlit as st

from dtower.tourney_results.constants import Graph, Options, all_relics, champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch


def compute_counts(df, options):
    df = df[~df.id.isin(get_sus_ids())]

    counts_for = [1, 10, 25, 50, 100]

    results = []

    for date, ddf in df.groupby("date"):
        result = {
            "date": date,
            "bc1": bcs[0].name if (bcs := ddf.iloc[0].bcs) else "",
            "bc2": bcs[1].name if (bcs := ddf.iloc[0].bcs) else "",
        }

        result |= {
            f"Top {count_for}": ddf.iloc[count_for - 1].wave if count_for <= len(ddf) else 0 for count_for in counts_for
        }
        results.append(result)

    to_be_displayed = pd.DataFrame(results).sort_values("date", ascending=False).reset_index(drop=True)
    st.dataframe(to_be_displayed)


if __name__ == "__main__":
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ], result_cutoff=200)
    compute_counts(df, options)