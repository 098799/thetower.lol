import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


from itertools import groupby

import pandas as pd
import streamlit as st

from dtower.sus.models import PlayerId
from dtower.tourney_results.formatting import make_player_url
from dtower.tourney_results.models import TourneyRow


def compute_search():
    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    real_name_part = st.text_input(
        "Enter part of the well-known player name to be queried (to be used for some people who never run with their discord names like Skye)"
    )

    if real_name_part:
        nickname_ids = list(
            PlayerId.objects.filter(player__name__icontains=real_name_part, primary=True).order_by("player_id").values_list("id", "player__name")[:100]
        )
    else:
        nickname_part = st.text_input("Enter part of the tourney name to be queried")

        if nickname_part:
            nickname_ids = list(TourneyRow.objects.filter(nickname__icontains=nickname_part).order_by("player_id").values_list("player_id", "nickname")[:100])
        else:
            player_id_part = st.text_input("Enter part of the player_id to be queried")

            if player_id_part:
                nickname_ids = list(
                    TourneyRow.objects.filter(player_id__icontains=player_id_part).order_by("player_id").values_list("player_id", "nickname")[:100]
                )
            else:
                exit()

    data_to_be_shown = []

    for player_id, nicknames in groupby(nickname_ids, lambda x: x[0]):
        nicknames = [nickname for _, nickname in nicknames]
        datum = {"player_id": make_player_url(player_id), "nicknames": ", ".join(set(nicknames)), "how_many_results": len(nicknames)}

        data_to_be_shown.append(datum)

    df = pd.DataFrame(data_to_be_shown)

    if not df.empty:
        df = df.sort_values("how_many_results", ascending=False)[:100]
        st.write(df[["player_id", "nicknames"]].to_html(escape=False, index=False), unsafe_allow_html=True)

    exit()


if __name__ == "__main__":
    compute_search()
