import streamlit as st

from components.results import Results
from dtower.tourney_results.constants import Graph, Options, leagues
from dtower.tourney_results.formatting import get_url, make_player_url
from dtower.tourney_results.models import TourneyResult


def compute_overview(options: Options):
    last_tourney = TourneyResult.objects.latest("date").date

    with open("style.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    with open("funny.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    for league in leagues:
        url = get_url(path=f"Results%20{league}")
        st.write(f"<h2><a href='{url}'>{league}</a></h2>", unsafe_allow_html=True)

        results = Results(options, league=league)
        to_be_displayed = results.prepare_data(current_page=1, step=10, date=last_tourney)
        to_be_displayed_styler = results.regular_preparation(to_be_displayed)
        st.write(
            to_be_displayed_styler.format(make_player_url, subset=["real_name"]).hide(axis="index").to_html(escape=False),
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    st.set_page_config(layout="centered")

    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    compute_overview(options)
