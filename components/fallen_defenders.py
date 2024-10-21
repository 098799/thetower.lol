import datetime

import pandas as pd
import streamlit as st

from components.util import deprecated, gantt
from dtower.tourney_results.constants import champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results


def compute_fallen_defenders(df):
    def style_df(df):
        return df[["Player", "When (days)", "Best wave", "Best #"]].style.apply(styling, axis=1)

    st.header("Fallen defenders")
    st.write("We're honoring the fallen defenders of yesteryear.")

    today = datetime.date.today()
    fallen = []
    reviewed = set()

    for date, ddf in df.groupby("date"):
        sdf = ddf[ddf.position <= 50]

        for player_id in sdf.id:
            if player_id in reviewed:
                continue

            pdf = df[df.id == player_id]
            last_date = pdf.date.max()
            last_seen = last_date - today

            if last_seen < datetime.timedelta(days=-14):
                best_wave = pdf.wave.max()
                wave_color = pdf[pdf.wave == best_wave].wave_role_color.iloc[0]
                best_position = pdf.position.min()
                position_color = pdf[pdf.position == best_position].position_role_color.iloc[0]
                player = pdf.iloc[0].real_name

                fallen.append(
                    {
                        "Player": player,
                        "days": last_seen.days,
                        "When (days)": -last_seen.days,
                        "Best wave": best_wave,
                        "wave_color": wave_color,
                        "Best #": best_position,
                        "position_color": position_color,
                        "tourneys_attended": sorted(pdf.date.unique()),
                    }
                )

            reviewed.add(player_id)

    fallen_df = pd.DataFrame(fallen).sort_values(["Best #", "days", "Best wave"]).reset_index(drop=True)

    fallen_champ = fallen_df[fallen_df["Best #"] == 1]
    fallen_other = fallen_df[fallen_df["Best #"] != 1]

    styling = lambda row: [
        None,
        None,
        f"color: {fallen_df[fallen_df['Player']==row['Player']].wave_color.iloc[0]}",
        f"color: {fallen_df[fallen_df['Player']==row['Player']].position_color.iloc[0]}",
    ]

    tbdf_champ = style_df(fallen_champ)
    tbdf_other = style_df(fallen_other)

    champ_col, other_col = st.columns([1, 1])
    champ_col.write("All hail fallen champions 🫡")
    other_col.write("May your labs still chug along")

    champ_col.dataframe(tbdf_champ, hide_index=True, height=600)
    other_col.dataframe(tbdf_other, hide_index=True, height=600)

    st.plotly_chart(gantt(fallen_champ))

    show_others = st.slider("Other fallen defenders", 0, len(fallen_other), (0, 40))
    st.plotly_chart(gantt(fallen_other[show_others[0] : show_others[1]]))


def get_fallen_defenders():
    deprecated()
    df = load_tourney_results(league_to_folder[champ])
    df = df[~df.id.isin(get_sus_ids())]
    compute_fallen_defenders(df)
