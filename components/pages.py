import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

import streamlit as st

from components.overview import compute_overview
from dtower.tourney_results.constants import Graph, Options, league_to_folder
from dtower.tourney_results.data import load_tourney_results

st.set_page_config(
    page_title="The Tower top200 tourney results",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "mailto:admin@thetower.lol",
    },
)

from st_pages import Page, Section, add_page_title, show_pages
from streamlit.source_util import invalidate_pages_cache

pages = [
    Page("components/overview.py", "Overview", "🏠"),
    Page("components/results.py", "Results Champions", "📈"),
    Page("components/results_plat.py", "Results Platinum", "📉"),
    Page("components/results_gold.py", "Results Gold", "🥇"),
    Page("components/results_silver.py", "Results Silver", "🥈"),
    Page("components/results_copper.py", "Results Copper", "🥉"),
    Page("components/player_lookup.py", "Player Lookup", "🔍"),
    Page("components/comparison.py", "Player Comparison", "🐶"),
    Page("components/winners.py", "Winners", "🔥"),
    Page("components/top_scores.py", "Top Scores", "📊"),
    Page("components/breakdown.py", "Breakdown", "📶"),
    Page("components/namechangers.py", "Namechangers", "☹️"),
    Page("components/about.py", "About", "🌚"),
]


hidden_features = os.environ.get("HIDDEN_FEATURES")

if hidden_features:
    pages += [
        Page("components/search_all_leagues.py", "Search all leagues", "🔨"),
    ]

show_pages(pages)
