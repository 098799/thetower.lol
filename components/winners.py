from collections import defaultdict

import pandas as pd
import plotly.express as px
import streamlit as st

from dtower.tourney_results.data import get_patches, load_tourney_results
from dtower.tourney_results.models import Patch

patches = sorted(get_patches(), key=lambda patch: patch.start_date, reverse=True)


def compute_winners(df, options=None):
    patch = st.selectbox("Limit results to a patch?", ["no", *patches])

    if isinstance(patch, Patch):
        df = df[df.patch == patch]

    how_col, hole_col = st.columns([1, 1])

    how_many = how_col.slider("How many past tournaments?", min_value=1, max_value=len(df[df.position == 1]), value=len(df[df.position == 1]))
    hole = hole_col.slider("Hole size?", min_value=0.0, max_value=1.0, value=0.3)

    dates = sorted(df.date.unique(), reverse=True)[:how_many]
    df = df[df.date.isin(dates)]

    scoring = st.selectbox("Scoring method?", ["Only winners", "5-3-2", "10-5-3-2-2-1-1-1-1-1", "bake your own"])

    skye_scoring = {1: 10, 2: 5, 3: 3, 4: 2, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1}

    additional_options = {"hole": hole}

    if scoring == "Only winners":
        winner_score = {1: 1, **dict(zip(range(2, 11), [0] * 9))}
    elif scoring == "5-3-2":
        winner_score = {1: 5, 2: 3, 3: 2, **dict(zip(range(4, 11), [0] * 9))}
    elif scoring == "10-5-3-2-2-1-1-1-1-1":
        winner_score = skye_scoring
    else:
        roll_columns = st.columns([1, 1, 1, 1, 1])
        winner_score = {
            place: roll_columns[(place - 1) % 5].slider(f"How many points for place {place}?", min_value=0, max_value=10, value=skye_scoring.get(place, 0))
            for place in range(1, 11)
        }
        colormap = st.selectbox("Color map?", [item for item in dir(px.colors.sequential) if not item.startswith("__") and not item.startswith("swatches")])
        additional_options = dict(color_discrete_sequence=getattr(px.colors.sequential, colormap))

    total_score = defaultdict(int)

    for position, score in winner_score.items():
        position_df = df[df.position == position]

        for real_name in position_df.real_name:
            total_score[real_name] += score

    total_score = {name: score for name, score in total_score.items() if score > 0}
    graph_df = pd.DataFrame(total_score.items(), columns=["name", "count"])

    fig = px.pie(graph_df, values="count", names="name", title="Winners of champ, courtesy of Jim", **additional_options)
    fig.update_traces(textinfo="value")
    st.plotly_chart(fig)


if __name__ == "__main__":
    df = load_tourney_results("data")
    compute_winners(df)
