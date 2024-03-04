import streamlit as st

from components.results import compute_results
from dtower.tourney_results.constants import Graph, Options, gold
from dtower.tourney_results.data import get_tourney_result_details
from dtower.tourney_results.models import TourneyResult

if __name__ == "__main__":
    st.set_page_config(layout="centered")
    options = Options(links_toggle=True, default_graph=Graph.last_16.value, average_foreground=True)
    # df = load_tourney_results(league_to_folder[gold], patch_id=Patch.objects.last().id)
    df = get_tourney_result_details(TourneyResult.objects.filter(league=gold).last(), offset=0, limit=1000)
    compute_results(df, options, league=gold)
