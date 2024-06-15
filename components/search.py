import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


from itertools import groupby

import streamlit as st
from django.db.models import Q

from components.util import add_player_id, add_to_comparison
from dtower.sus.models import PlayerId
from dtower.tourney_results.constants import how_many_results_public_site
from dtower.tourney_results.models import TourneyRow


def compute_search(player=False, comparison=False):
    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    name_col, id_col = st.columns([1, 1])

    page = 20

    real_name_part = name_col.text_input("Enter part of the player name")

    if real_name_part:
        nickname_ids = list(
            PlayerId.objects.filter(
                player__name__istartswith=real_name_part,
                primary=True,
            )
            .order_by("player_id")
            .values_list("id", "player__name")[:page]
        )

        if len(nickname_ids) < page:
            nickname_ids += list(
                TourneyRow.objects.filter(
                    ~Q(player_id__in=[player_id for player_id, _ in nickname_ids]),
                    nickname__istartswith=real_name_part,
                    position__lte=how_many_results_public_site,
                )
                .distinct()
                .order_by("player_id")
                .values_list("player_id", "nickname")[: page - len(nickname_ids)]
            )

        if len(nickname_ids) < page:
            nickname_ids += list(
                PlayerId.objects.filter(
                    ~Q(id__in=[player_id for player_id, _ in nickname_ids]),
                    player__name__icontains=real_name_part,
                    primary=True,
                )
                .order_by("player_id")
                .values_list("id", "player__name")[:page]
            )

        if len(nickname_ids) < page:
            nickname_ids += list(
                TourneyRow.objects.filter(
                    ~Q(player_id__in=[player_id for player_id, _ in nickname_ids]),
                    nickname__icontains=real_name_part,
                    position__lte=how_many_results_public_site,
                )
                .distinct()
                .order_by("player_id")
                .values_list("player_id", "nickname")[: page - len(nickname_ids)]
            )
    else:
        player_id_part = id_col.text_input("Enter part of the player_id to be queried")

        if player_id_part:
            nickname_ids = list(
                TourneyRow.objects.filter(
                    player_id__icontains=player_id_part,
                    position__lte=how_many_results_public_site,
                )
                .order_by("player_id")
                .values_list("player_id", "nickname")[:page]
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

        if player:
            button_col.button("See player page", on_click=add_player_id, args=(datum["player_id"],), key=f'{datum["player_id"]}but')

        if comparison:
            comp_col.button("Add to comparison", on_click=add_to_comparison, args=(datum["player_id"], datum["nicknames"]), key=f'{datum["player_id"]}comp')

    if not data_to_be_shown:
        st.info("No results found")

    return data_to_be_shown


if __name__ == "__main__":
    compute_search()
