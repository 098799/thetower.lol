import pandas as pd
import streamlit as st

from dtower.sus.models import PlayerId
from dtower.tourney_results.constants import champ, legend
from dtower.tourney_results.data import get_sus_ids
from dtower.tourney_results.formatting import make_player_url
from dtower.tourney_results.models import TourneyRow


def get_namechangers():
    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    id_data = PlayerId.objects.all().select_related("player__name").values("id", "player__name", "primary")
    iddf = pd.DataFrame(id_data)
    iddf = iddf.rename(columns={"player__name": "real_name"})

    piddf = iddf[iddf.primary]
    real_name_id_mapping = dict(zip(piddf.real_name, piddf.id))
    id_real_name_mapping = dict(zip(iddf.id, iddf.real_name))

    all_ids = iddf.id.unique()

    rows = (
        TourneyRow.objects.all()
        .select_related("result")
        .filter(player_id__in=all_ids, result__league__in=[champ, legend])
        .values("player_id", "nickname", "wave", "result__date")
        .order_by("-result__date")
    )
    rdf = pd.DataFrame(rows)

    rdf["real_name"] = [id_real_name_mapping[id] for id in rdf.player_id]
    # populate with primary ids only, such that it's unique
    rdf["player_id"] = [real_name_id_mapping[real_name] for real_name in rdf.real_name]

    rdf = rdf[~rdf.player_id.isin(get_sus_ids())]
    rdf = rdf.rename(columns={"player_id": "id", "nickname": "tourney_name"})

    combined_data = []

    df = rdf

    for id, data in df.groupby("id"):
        if len(data.tourney_name.unique()) == 1:
            continue

        real_name = data.real_name.iloc[0]
        how_many_rows = len(data)
        how_many_names = len(data.tourney_name.unique())
        # last_performance = data[-5:].wave.mean()

        combined_data.append(
            {
                "real_name": real_name,
                "id": id,
                "namechanged_times": how_many_names,
                "total": how_many_rows,
                # "mean_last_5_tourneys": int(round(last_performance, 0)),
            }
        )

    new_df = pd.DataFrame(combined_data)
    new_df = new_df.sort_values("namechanged_times", ascending=False).reset_index(drop=True)

    to_be_displayed = new_df.style.format(make_player_url, subset=["id"])

    st.write(to_be_displayed.to_html(escape=False, index=False), unsafe_allow_html=True)
