from collections import Counter

import pandas as pd
import streamlit as st

from components.util import deprecated
from dtower.tourney_results.constants import Graph, Options, all_relics, champ, league_to_folder
from dtower.tourney_results.data import load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch


def compute_various(df, options):
    width = 48
    legend_width = 128
    numerals = ["1st", "2nd", "3rd"]

    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    patches = list(Patch.objects.filter(version_minor__gte=20))
    df = df[df.patch.isin(patches)]

    podiums = []

    for date, subdf in sorted(df.groupby("date"), reverse=True):
        counter = Counter([avatar for avatar in subdf.avatar if avatar])
        podium = [avatar for avatar, count in counter.most_common(3)]
        counts = [int(count / len(subdf) * 100) for _, count in counter.most_common(3)]

        # get_extension = lambda x: "webp" if x in [35, 36, 39, 42, 44, 45, 46] else "png"
        get_extension = "png"

        pod = {"date": date}
        pod |= {
            numeral: f"<img src='./app/static/Tower_Skins/{spot}.{get_extension(spot)}' width='{width}'> -- {count}%"
            for spot, count, numeral in zip(podium, counts, numerals)
        }

        podiums.append(pod)

    podium_df = pd.DataFrame(podiums).set_index("date")
    podium_df.index.name = None

    st.header("Popular avatars")
    st.write(podium_df.to_html(escape=False), unsafe_allow_html=True)

    seen_relics = set()
    podiums = []

    for date, subdf in sorted(df.groupby("date"), reverse=True):
        counter = Counter([relic for relic in subdf.relic if relic > -1])
        podium = [relic for relic, _ in counter.most_common(3)]
        counts = [int(count / len(subdf) * 100) for _, count in counter.most_common(3)]
        seen_relics |= set(podium)

        podium_titles = [all_relics[pod][0] if pod in all_relics else "" for pod in podium]
        podium_relics_1 = [all_relics[pod][1] if pod in all_relics else "" for pod in podium]
        podium_relics_2 = [all_relics[pod][2] if pod in all_relics else "" for pod in podium]

        pod = {"date": date}

        # get_extension = lambda x: "webp" if x in [48, 49, 50, 51, 52, 53, 60, 61] else "png"
        get_extension = "png"

        pod |= {
            numeral: f"<img src='./app/static/Tower_Relics/{spot}.{get_extension(spot)}' width='{width}' title='{title}, {relic_1} {relic_2}'> -- {count}%"
            for spot, title, relic_1, relic_2, numeral, count in zip(podium, podium_titles, podium_relics_1, podium_relics_2, numerals, counts)
        }
        podiums.append(pod)

    podium_df = pd.DataFrame(podiums).set_index("date")
    podium_df.index.name = None

    st.header("Popular relics")
    st.write(podium_df.to_html(escape=False), unsafe_allow_html=True)

    st.header("Legend:")

    for relic in sorted(seen_relics):
        if relic in all_relics:
            name, bonus, what = all_relics[relic]
            st.write(
                f"<img src='./app/static/Tower_Relics/{relic}.png' width='{legend_width}'> -- {name}, {bonus} {what}",
                unsafe_allow_html=True,
            )


def get_various():
    deprecated()
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ])
    compute_various(df, options)
