import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


from itertools import groupby

import streamlit as st

from components.util import add_player_id, add_to_comparison
from dtower.sus.models import PlayerId
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
        datum = {"player_id": player_id, "nicknames": ", ".join(set(nicknames)), "how_many_results": len(nicknames)}

        data_to_be_shown.append(datum)

    for datum in data_to_be_shown:
        nickname_col, player_id_col, button_col, comp_col = st.columns([1, 1, 1, 1])
        nickname_col.write(datum["nicknames"])
        player_id_col.write(datum["player_id"])
        button_col.button("See player page", on_click=add_player_id, args=(datum["player_id"],), key=f'{datum["player_id"]}but')
        comp_col.button("Add to comparison", on_click=add_to_comparison, args=(datum["player_id"],), key=f'{datum["player_id"]}comp')


if __name__ == "__main__":
    compute_search()
