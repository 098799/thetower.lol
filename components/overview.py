import pandas as pd
import streamlit as st

from components.results import Results
from dtower.tourney_results.constants import Options


def compute_overview(dfs, options: Options):
    overall_df = pd.concat(dfs)
    last_tourney = sorted(overall_df.date.unique())[-1]

    for df in dfs:
        filtered_df = df[df.date == last_tourney]
        filtered_df = filtered_df.reset_index(drop=True)

        if filtered_df.empty:
            continue

        results = Results(filtered_df, options)
        to_be_displayed = results.prepare_data(filtered_df, how_many=10)
        to_be_displayed_styler = results.regular_preparation(to_be_displayed, filtered_df)
        st.dataframe(to_be_displayed_styler, use_container_width=True)
