import pandas as pd
import streamlit as st

from dtower.tourney_results.constants import league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.formatting import color_position
from dtower.tourney_results.models import PatchNew as Patch
from dtower.tourney_results.models import Role

league_to_color = {league: Role.objects.filter(league=league).last().color for league in league_to_folder.keys()}


def compute_sus_overview(df, *args, **kwargs):
    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    data = get_impossible_avatars(df)

    if not data.empty:
        st.subheader("Impossible avatars not sused yet:")
        st.write(data.to_html(escape=False), unsafe_allow_html=True)
        st.write("")
    else:
        st.subheader("No impossible avatars")

    data = get_copper_to_champ(df)

    if data:
        st.subheader("Potential sus copper to champ (last 7 tourneys):")

        names = ["/".join(set(datum.tourney_name)) for datum in data]
        ids = ["/".join(set(datum.id)) for datum in data]
        leagues = ["/".join(set(datum.league)) for datum in data]

        summary = pd.DataFrame({"name": names, "ids": ids, "leagues": leagues, "sus_me_daddy": [datum.sus_him.iloc[0] for datum in data]})

        st.write(summary.to_html(escape=False), unsafe_allow_html=True)
        st.write("")

        for datum in data:
            tbdf = datum.style.apply(lambda row: [None, None, None, None, None, f"color: {league_to_color[row.league]}", None], axis=1).map(
                color_position, subset=["position"]
            )

            st.write(tbdf.to_html(escape=False), unsafe_allow_html=True)
            st.write("")
    else:
        st.subheader("No potential unsussed copper to champ")


def get_impossible_avatars(df):
    def make_sus_link(id, name, avatar, date):
        return f"<a href='http://admin.thetower.lol/admin/sus/susperson/add/?player_id={id}&name={name}&notes=impossible avatar {avatar} {date.isoformat()}' target='_blank'>🔗 sus him</a>"

    impossible_avatars = {
        25: "panda",
        26: "ttg logo",
    }

    df = df[~df.id.isin(get_sus_ids())]
    avatars_df = df[df.avatar.isin(impossible_avatars.keys())]

    avatars_df = avatars_df[["id", "tourney_name", "wave", "date", "league", "avatar"]]
    avatars_df.avatar = avatars_df.avatar.map(impossible_avatars)
    avatars_df["sus_him"] = [
        make_sus_link(id, name, avatar, date)
        for id, name, avatar, date in zip(
            avatars_df.id,
            avatars_df.tourney_name,
            avatars_df.avatar,
            avatars_df.date,
        )
    ]
    return avatars_df


def get_copper_to_champ(df):
    def make_sus_link(id, name, date):
        return f"<a href='http://admin.thetower.lol/admin/sus/susperson/add/?player_id={id}&name={name}&notes=potential coppper-champ {date.isoformat()}' target='_blank'>🔗 sus him</a>"

    data = []

    df = df[~df.id.isin(get_sus_ids())]

    for id, player_df in df.groupby("id"):
        leagues = sorted(player_df.league)

        if len(leagues) < 7 and len(set(leagues)) >= 3 and "Copper" in leagues:
            player_df = player_df[["id", "tourney_name", "wave", "position", "date", "league"]]
            player_df["sus_him"] = [
                make_sus_link(id, name, date)
                for id, name, date in zip(
                    player_df.id,
                    player_df.tourney_name,
                    player_df.date,
                )
            ]

            data.append(player_df.sort_values("date", ascending=False).reset_index(drop=True))

    return data


if __name__ == "__main__":
    last_patch = Patch.objects.last()

    dfs = [load_tourney_results(league, limit_no_results=7) for league in league_to_folder.values()]

    for df, league in zip(dfs, league_to_folder.keys()):
        df["league"] = league

    df = pd.concat(dfs)

    compute_sus_overview(df)
