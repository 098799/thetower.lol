import streamlit as st

from components.results import compute_results
from dtower.tourney_results.constants import Graph, Options, silver

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    options = Options(links_toggle=True, default_graph=Graph.last_16.value, average_foreground=True)
    compute_results(options, league=silver)
