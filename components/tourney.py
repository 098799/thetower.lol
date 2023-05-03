import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


import datetime
import os
from typing import List, Optional

import pandas as pd
import streamlit as st

from components.about import compute_about
from components.breakdown import compute_breakdown
from components.comparison import compute_comparison
from components.constants import Graph, Options
from components.data import get_manager, load_tourney_results
from components.namechangers import compute_namechangers
from components.player_lookup import compute_player_lookup
from components.results import compute_results
from components.search_all_leagues import compute_search_all_leagues
from components.top_scores import compute_top
from components.winners import compute_winners
from dtower.tourney_results.constants import league_to_folder

st.set_page_config(
    page_title="The Tower top200 tourney results",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "mailto:admin@thetower.lol",
    },
)

st.write(
    """<style>
.stRadio div {
    display: inline;
}
.stRadio > div > label {
    border-bottom: 1px solid #26282e;
    display: inline-block;
    padding: 4px 8px 4px 0px;
    margin: 0px;
    border-radius: 4px 4px 0 0;
    position: relative;
    top: 1px;
    # border-left: 5px solid #F63366;
}
.stRadio > div > label :hover {
    color: #F63366;
}
.stRadio input:checked + div {
    color: #F63366;
    border-left: 5px solid #F63366;
}
</style>
    """,
    unsafe_allow_html=True,
)


# st.error("This site is currently suspended until the hacker situation is resolved.")


with st.sidebar:
    st.write("Toggles")

    links = st.checkbox("Links to users? (will make dataframe ugly)", value=get_manager().get("links"))

    congrats_cookie_value = get_manager().get("congrats")
    default_graph_value = get_manager().get("default_graph")
    average_foreground_value = get_manager().get("average_foreground")

    congrats_toggle = st.checkbox("Do you like seeing congratulations?", value=congrats_cookie_value if congrats_cookie_value is not None else True)

    graph_choices: List[str] = list(Graph.__members__.keys())
    default_graph = st.radio(
        "How should the player data be presented by default?",
        graph_choices,
        index=graph_choices.index(default_graph_value if default_graph_value is not None else "all"),
    )

    average_foreground = st.checkbox("Rolling averages as default in graphs?", value=average_foreground_value if average_foreground_value is not None else True)

    get_manager().set("links", links, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="links")
    get_manager().set("congrats", bool(congrats_toggle), expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="congrats")
    get_manager().set("default_graph", default_graph, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="default_graph")
    get_manager().set("average_foreground", default_graph, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="average_foreground")

    options = Options(congrats_toggle=congrats_toggle, links_toggle=links, default_graph=default_graph, average_foreground=average_foreground)


pd.set_option("display.max_rows", None)


###############
### tab layout setup
###############

query = st.experimental_get_query_params()

if query:
    print(datetime.datetime.now(), query)

current_player: Optional[str]
compare_players: Optional[List[str]]

player = query.get("player")
compare_players = st.experimental_get_query_params().get("compare")

if player:
    current_player = player[0]
    functionality = "Player lookup"
elif compare_players:
    current_player = None
    functionality = "Comparison"
else:
    current_player = None
    functionality = None

options.current_player = current_player
options.compare_players = compare_players


league_switcher = os.environ.get("LEAGUE_SWITCHER")

tabs = ["Results", "Player lookup", "Winners", "Comparison", "Top", "Breakdown", "Namechangers", "About"]

if league_switcher:
    league: str = st.radio("Which league?", list(league_to_folder.keys()), index=0)
    tabs.append("Search all leagues")
else:
    league = "Champions"

functionality: str = st.radio("Which functionality to show?", tabs, index=0 if not functionality else tabs.index(functionality))


def keep():
    compute_results
    compute_player_lookup
    compute_comparison
    compute_winners
    compute_top
    compute_breakdown
    compute_about
    compute_namechangers
    compute_search_all_leagues


function_string = f"compute_{'_'.join(functionality.lower().split())}"

if function_string == "compute_search_all_leagues":
    leagues = sorted(league_to_folder.items())
    dfs = [load_tourney_results(league) for _, league in leagues]

    for df, (league, _) in zip(dfs, leagues):
        df["league"] = league

    df = pd.concat(dfs)
else:
    df = load_tourney_results(league_to_folder[league])

function = globals()[function_string]
function(df, options)
