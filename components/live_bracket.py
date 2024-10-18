import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from components.comparison import compute_comparison
from dtower.tourney_results.data import get_player_id_lookup


def get_time(file_path: Path) -> datetime.datetime:
    return datetime.datetime.strptime(str(file_path.stem), "%Y-%m-%d__%H_%M")


def live_bracket():
    home = Path.home()
    live_path = home / "tourney" / "results_cache" / "Champion_live"

    all_files = live_path.glob("*.csv")
    data = {get_time(file): pd.read_csv(file) for file in all_files}

    for dt, df in data.items():
        df["datetime"] = dt

    if not data:
        return st.info("No current data, wait until the tourney day")

    df = pd.concat(data.values())
    df = df.sort_values(["datetime", "wave"], ascending=False)

    lookup = get_player_id_lookup()
    df["real_name"] = [lookup.get(id, name) for id, name in zip(df.player_id, df.name)]

    selected_real_name = st.selectbox("Bracket of...", [""] + sorted(df.real_name.unique()))

    if selected_real_name:
        sdf = df[df.real_name == selected_real_name]
        bracket_id = sdf.bracket.iloc[0]

        tdf = df[df.bracket == bracket_id]
        player_ids = sorted(tdf.player_id.unique())

        tdf["datetime"] = pd.to_datetime(tdf["datetime"])
        fig = px.line(tdf, x="datetime", y="wave", color="real_name", title="Live bracket score", markers=True, line_shape="linear")
        fig.update_traces(mode="lines+markers")
        fig.update_layout(xaxis_title="Time", yaxis_title="Wave", legend_title="real_name", hovermode="closest")
        st.plotly_chart(fig)

        st.session_state.display_comparison = True
        st.session_state.options.compare_players = player_ids
        compute_comparison(sdf.player_id.iloc[0])
