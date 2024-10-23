import pandas as pd
import plotly.express as px
import streamlit as st

from components.comparison import compute_comparison
from components.live_score import get_live_df
from components.util import get_options
from dtower.tourney_results.constants import champ, legend


def live_bracket():
    tabs = st.tabs([legend, champ])

    for tab, league in zip(tabs, [legend, champ]):
        options = get_options(links=False)

        try:
            df = get_live_df(league)
        except (IndexError, ValueError):
            tab.info("No current data, wait until the tourney day")
            continue

        name_col, id_col = tab.columns(2)

        selected_real_name = None
        selected_player_id = None

        if options.current_player:
            selected_real_name = options.current_player
        else:
            if options.current_player_id:
                selected_player_id = options.current_player_id
            else:
                selected_real_name = name_col.selectbox("Bracket of...", [""] + sorted(df.real_name.unique()))

        if not selected_real_name and not selected_player_id:
            selected_player_id = id_col.selectbox("...or by player id", [""] + sorted(df.player_id.unique()))

            if not selected_player_id:
                continue

        if selected_player_id:
            try:
                selected_real_name = df[df.player_id == selected_player_id].real_name.iloc[0]
            except Exception:
                st.error("Player id not found")
                exit()

        if selected_real_name:
            try:
                sdf = df[df.real_name == selected_real_name]
            except Exception:
                st.error("Player name not found")
                exit()

            bracket_id = sdf.bracket.iloc[0]

            tdf = df[df.bracket == bracket_id]
            player_ids = sorted(tdf.player_id.unique())

            tdf["datetime"] = pd.to_datetime(tdf["datetime"])
            fig = px.line(tdf, x="datetime", y="wave", color="real_name", title="Live bracket score", markers=True, line_shape="linear")
            fig.update_traces(mode="lines+markers")
            fig.update_layout(xaxis_title="Time", yaxis_title="Wave", legend_title="real_name", hovermode="closest")
            tab.plotly_chart(fig, use_container_width=True)

            last_moment = tdf.datetime.max()
            ldf = tdf[tdf.datetime == last_moment].reset_index(drop=True)
            ldf.index = ldf.index + 1
            tab.dataframe(ldf[["player_id", "name", "real_name", "wave", "datetime"]])

            st.session_state.display_comparison = True
            st.session_state.options.compare_players = player_ids
            compute_comparison(sdf.player_id.iloc[0], canvas=tab)
