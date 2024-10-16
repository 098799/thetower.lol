import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from functools import partial

import streamlit as st

from components.about import compute_about
from components.breakdown import compute_breakdown
from components.comparison import get_comparison
from components.counts import compute_counts
from components.fallen_defenders import get_fallen_defenders
from components.live_bracket import live_bracket
from components.live_score import live_score
from components.namechangers import get_namechangers
from components.overview import compute_overview
from components.player import compute_player_lookup
from components.results import compute_results
from components.sus_overview import get_sus_overview
from components.top_scores import get_top_scores
from components.various import get_various
from components.winners import compute_winners
from dtower.tourney_results.constants import Graph, Options, legend, champ, copper, gold, plat, silver

st.set_page_config(
    page_title="The Tower top200 tourney results",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "mailto:admin@thetower.lol",
    },
)


options = Options(links_toggle=True, default_graph=Graph.last_16.value, average_foreground=True)


if st.session_state.get("options") is None:
    st.session_state.options = options


pages = [
    st.Page(partial(compute_overview, options=options), title="Overview", icon="🏠", url_path="overview"),
    st.Page(partial(compute_results, league=legend, options=options), title="Results Legend", icon="🏆", url_path="legend"),
    st.Page(partial(compute_results, league=champ, options=options), title="Results Champion", icon="🏆", url_path="champion"),
    st.Page(partial(compute_results, league=plat, options=options), title="Results Platinum", icon="📉", url_path="platinum"),
    st.Page(partial(compute_results, league=gold, options=options), title="Results Gold", icon="🥇", url_path="gold"),
    st.Page(partial(compute_results, league=silver, options=options), title="Results Silver", icon="🥈", url_path="silver"),
    st.Page(partial(compute_results, league=copper, options=options), title="Results Copper", icon="🥉", url_path="copper"),
    st.Page(compute_player_lookup, title="Player", icon="⛹️", url_path="player"),
    st.Page(get_comparison, title="Player Comparison", icon="🔃", url_path="comparison"),
    st.Page(compute_winners, title="Winners", icon="🔥", url_path="winners"),
    st.Page(get_top_scores, title="Top Scores", icon="🤑", url_path="top"),
    st.Page(partial(compute_breakdown, options=options), title="Breakdown", icon="🪁", url_path="breakdown"),
    st.Page(get_namechangers, title="Namechangers", icon="💩", url_path="namechangers"),
    st.Page(get_various, title="Relics and Avatars", icon="👽", url_path="relics"),
    st.Page(compute_counts, title="Wave cutoff (counts)", icon="🐈", url_path="counts"),
    st.Page(get_fallen_defenders, title="Fallen defenders", icon="🪦", url_path="fallen"),
    st.Page(compute_about, title="About", icon="👴", url_path="about"),
]


hidden_features = os.environ.get("HIDDEN_FEATURES")

if hidden_features:
    pages += [
        st.Page(get_sus_overview, title="SUS overview", icon="🔨", url_path="sus"),
        st.Page(live_score, title="live score", icon="⏱️", url_path="live"),
        st.Page(live_bracket, title="bracket", icon="🔠", url_path="bracket"),
    ]

pg = st.navigation(pages)
pg.run()
