import os

import streamlit as st

from components.results import Results
from dtower.tourney_results.constants import Graph, Options, champ, leagues, legend
from dtower.tourney_results.formatting import get_url
from dtower.tourney_results.models import TourneyResult


def compute_overview(options: Options):
    public = {"public": True} if not os.environ.get("HIDDEN_FEATURES") else {}
    last_tourney = TourneyResult.objects.filter(**public).latest("date")
    last_tourney_date = last_tourney.date

    with open("style.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    with open("funny.css", "r") as infile:
        st.write(f"<style>{infile.read()}</style>", unsafe_allow_html=True)

    # st.markdown(get_summary())
    if overview := TourneyResult.objects.filter(league=legend, **public).latest("date").overview:
        st.markdown(overview, unsafe_allow_html=True)

    for league in leagues:
        url = get_url(path=league.lower() if league != champ else "results")
        st.write(f"<h2><a href='{url}'>{league}</a></h2>", unsafe_allow_html=True)

        results = Results(options, league=league)
        to_be_displayed = results.prepare_data(current_page=1, step=11, date=last_tourney_date)

        if to_be_displayed is None:
            st.warning("Failed to display results, likely loss of data.")
            return None

        to_be_displayed_styler = results.regular_preparation(to_be_displayed)
        st.write(
            to_be_displayed_styler.hide(axis="index").to_html(escape=False),
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    st.set_page_config(layout="centered")

    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    compute_overview(options)
