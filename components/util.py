import datetime
from typing import List, Optional

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
