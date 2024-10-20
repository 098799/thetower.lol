import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from dtower.tourney_results.constants import Graph, Options


def links_toggle():
    with st.sidebar:
        st.write("Toggles")
        links = st.checkbox("Links to users? (will make dataframe ugly)", value=False)

    return links


def get_options(links=None):
    if links is not False:
        links = links_toggle()

    options = Options(links_toggle=links, default_graph=Graph.last_16.value, average_foreground=True)

    query = st.query_params

    if query:
        print(datetime.datetime.now(), query)

    player = query.get("player")
    player_id = query.get("player_id")
    compare_players = query.get_all("compare")
    print(f"{player=}, {compare_players=}")

    options.current_player = player
    options.current_player_id = player_id
    options.compare_players = compare_players

    return options


def gantt(df):
    def get_borders(dates: list[datetime.date]) -> list[tuple[datetime.date, datetime.date]]:
        """Get start and finish of each interval. Assuming dates are sorted and tourneys are max 4 days apart."""

        borders = []

        start = dates[0]

        for date, next_date in zip(dates[1:], dates[2:]):
            if next_date - date > datetime.timedelta(days=4):
                end = date
                borders.append((start, end))
                start = next_date

        borders.append((start, dates[-1]))

        return borders

    gantt_data = []

    for i, row in df.iterrows():
        borders = get_borders(row.tourneys_attended)
        name = row.Player

        for start, end in borders:
            gantt_data.append(
                {
                    "Player": name,
                    "Start": start,
                    "Finish": end,
                    "Champion": name,
                }
            )

    gantt_df = pd.DataFrame(gantt_data)

    fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Player", color="Champion")
    fig.update_yaxes(autorange="reversed")
    return fig


def add_player_id(player_id):
    st.session_state.player_id = player_id


def add_to_comparison(player_id, nicknames):
    if "comparison" in st.session_state:
        st.session_state.comparison.add(player_id)
        st.session_state.addee_map[player_id] = nicknames
    else:
        st.session_state.comparison = {player_id}
        st.session_state.addee_map = {player_id: nicknames}

    print(f"{st.session_state.comparison=} {st.session_state.addee_map=}")
    st.session_state.counter = st.session_state.counter + 1 if st.session_state.get("counter") else 1
