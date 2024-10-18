import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from components.comparison import compute_comparison
from components.live_score import get_live_df


def get_time(file_path: Path) -> datetime.datetime:
    return datetime.datetime.strptime(str(file_path.stem), "%Y-%m-%d__%H_%M")


def live_bracket():
    df = get_live_df()

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
