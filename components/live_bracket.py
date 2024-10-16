import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from components.comparison import compute_comparison
from thetower.dtower.tourney_results.data import get_player_id_lookup


def get_time(file_path: Path) -> datetime.datetime:
    return datetime.datetime.strptime(str(file_path.stem), "%Y-%m-%d__%H_%M")


def live_bracket():
    home = Path.home()
    live_path = home / "tourney" / "results_cache" / "Champion_live"

    all_files = live_path.glob("*.csv")
    data = {get_time(file): pd.read_csv(file) for file in all_files}

    for dt, df in data.items():
        df["datetime"] = dt

    df = pd.concat(data.values())
    df = df.sort_values(["datetime", "wave"], ascending=False)

    top_10 = df.head(10).player_id.tolist()
    lookup = get_player_id_lookup()
    df["real_name"] = [lookup.get(id, name) for id, name in zip(df.player_id, df.name)]
    tdf = df[df.player_id.isin(top_10)]

    # last_moment = tdf.datetime.iloc[0]
    # ldf = df[df.datetime == last_moment]

    tdf["datetime"] = pd.to_datetime(tdf["datetime"])
    # fig = px.line(tdf, x="datetime", y="wave", color="real_name", title="Top 10 Players: live score", markers=True, line_shape="linear")

    # fig.update_traces(mode="lines+markers")
    # fig.update_layout(xaxis_title="Time", yaxis_title="Wave", legend_title="real_name", hovermode="closest")
    # st.plotly_chart(fig)

    # summary = get_summary(df[["real_name", "wave", "datetime"]].to_markdown(index=False))

    # st.markdown(summary)

    # st.dataframe(ldf[["real_name", "wave", "datetime"]])

    selected_real_name = st.selectbox("Bracket of...", [""] + sorted(df.real_name.unique()))

    if selected_real_name:
        sdf = df[df.real_name == selected_real_name]
        bracket_id = sdf.bracket.iloc[0]
        player_ids = sorted(df[df.bracket == bracket_id].player_id.unique())

        st.session_state.display_comparison = True
        st.session_state.options.compare_players = player_ids
        compute_comparison(sdf.player_id.iloc[0])
