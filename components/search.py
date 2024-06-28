import os
from functools import reduce
from operator import and_, or_

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
    # id_col.checkbox("Search by player_id", key="search_by_id")
    # st.image

    fragments = [part.strip() for part in real_name_part.strip().split()]

    if fragments:
        match_part = reduce(and_, [Q(player__name__icontains=fragment) for fragment in fragments[1:]]) if fragments[1:] else Q()

        nickname_ids = list(
            PlayerId.objects.filter(
                Q(player__name__istartswith=fragments[0]) & match_part,
                primary=True,
            )
            .order_by("player_id")
            .values_list("id", "player__name")[:page]
        )

        if len(nickname_ids) < page:
            match_part = reduce(and_, [Q(nickname__icontains=fragment) for fragment in fragments[1:]]) if fragments[1:] else Q()

            nickname_ids += list(
                TourneyRow.objects.filter(
                    ~Q(player_id__in=[player_id for player_id, _ in nickname_ids]),
                    Q(nickname__istartswith=fragments[0]) & match_part,
                    position__lte=how_many_results_public_site,
                )
                .distinct()
                .order_by("player_id")
                .values_list("player_id", "nickname")[: page - len(nickname_ids)]
            )

        if len(nickname_ids) < page:
            query = reduce(and_, [Q(player__name__icontains=fragment) for fragment in fragments])

            nickname_ids += list(
                PlayerId.objects.filter(
                    ~Q(id__in=[player_id for player_id, _ in nickname_ids]),
                    query,
                    primary=True,
                )
                .order_by("player_id")
                .values_list("id", "player__name")[:page]
            )

        if len(nickname_ids) < page:
            query = reduce(and_, [Q(nickname__icontains=fragment) for fragment in fragments])

            nickname_ids += list(
                TourneyRow.objects.filter(
                    ~Q(player_id__in=[player_id for player_id, _ in nickname_ids]),
                    query,
                    position__lte=how_many_results_public_site,
                )
                .distinct()
                .order_by("player_id")
                .values_list("player_id", "nickname")[: page - len(nickname_ids)]
            )
    else:
        player_id_part = id_col.text_input("Enter part of the player_id to be queried")
        player_id_fragments = [part.strip() for part in player_id_part.strip().split()]

        if player_id_fragments:
            match_part = reduce(and_, [Q(player_id__icontains=fragment) for fragment in player_id_fragments[1:]]) if player_id_fragments[1:] else Q()

            nickname_ids_data = (
                TourneyRow.objects.filter(
                    Q(player_id__istartswith=player_id_fragments[0]) & match_part,
                    position__lte=how_many_results_public_site,
                )
                .order_by("player_id")
                .values_list("player_id", "nickname")
            )

            nickname_ids = []

            for _, group in groupby(sorted(nickname_ids_data), lambda x: x[0]):
                group = list(group)
                nickname_ids.append((group[0][0], ", ".join(list(set(nickname for _, nickname in group))[:page])))
        else:
            exit()

    data_to_be_shown = []

    for player_id, nicknames in groupby(nickname_ids, lambda x: x[0]):
        nicknames = [nickname for _, nickname in nicknames]
        datum = {"player_id": player_id, "nicknames": ", ".join(set(nicknames)), "how_many_results": len(nicknames)}

        data_to_be_shown.append(datum)

    for datum in data_to_be_shown:
        nickname_col, player_id_col, button_col = st.columns([1, 1, 1])
        nickname_col.write(datum["nicknames"])
        player_id_col.write(datum["player_id"])

        if player:
            button_col.button("See player page", on_click=add_player_id, args=(datum["player_id"],), key=f'{datum["player_id"]}{datum["nicknames"]}but')

        if comparison:
            button_col.button("Add to comparison", on_click=add_to_comparison, args=(datum["player_id"], datum["nicknames"]), key=f'{datum["player_id"]}comp')

    if not data_to_be_shown:
        st.info("No results found")

    return data_to_be_shown


if __name__ == "__main__":
    compute_search()
