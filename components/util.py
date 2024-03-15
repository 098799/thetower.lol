import datetime
from typing import List, Optional

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

    query = st.experimental_get_query_params()

    if query:
        print(datetime.datetime.now(), query)

    current_player: Optional[str] = None
    compare_players: Optional[List[str]]

    player = query.get("player")
    compare_players = st.experimental_get_query_params().get("compare")

    if player:
        current_player = player[0]

    options.current_player = current_player
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
