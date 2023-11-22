from collections import Counter

import pandas as pd
import streamlit as st

from dtower.tourney_results.constants import Graph, Options, all_relics, champ, league_to_folder
from dtower.tourney_results.data import load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch


def compute_various(df, options):
    width = 48
    legend_width = 128

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
        podiums.append(
            {
                "date": date,
                "1st": f"<img src='./app/static/Tower_Skins/{podium[0]}.png' width='{width}'> -- {counts[0]}%",
                "2nd": f"<img src='./app/static/Tower_Skins/{podium[1]}.png' width='{width}'> -- {counts[1]}%",
                "3rd": f"<img src='./app/static/Tower_Skins/{podium[2]}.png' width='{width}'> -- {counts[2]}%",
            }
        )

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

        podiums.append(
            {
                "date": date,
                "1st": f"<img src='./app/static/Tower_Relics/{podium[0]}.png' width='{width}' title='{podium_titles[0]}, {podium_relics_1[0]} {podium_relics_2[0]}'> -- {counts[0]}%",
                "2nd": f"<img src='./app/static/Tower_Relics/{podium[1]}.png' width='{width}' title='{podium_titles[1]}, {podium_relics_1[1]} {podium_relics_2[1]}'> -- {counts[1]}%",
                "3rd": f"<img src='./app/static/Tower_Relics/{podium[2]}.png' width='{width}' title='{podium_titles[2]}, {podium_relics_1[2]} {podium_relics_2[2]}'> -- {counts[2]}%",
            }
        )

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


if __name__ == "__main__":
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ])
    compute_various(df, options)
