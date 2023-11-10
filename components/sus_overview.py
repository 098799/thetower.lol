import streamlit as st

from dtower.tourney_results.constants import league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch


def compute_sus_overview(df, *args, **kwargs):
    data = get_impossible_avatars(df)

    if not data.empty:
        st.subheader("Impossible avatars not sused yet:")
        st.write(data.to_html(escape=False), unsafe_allow_html=True)
    else:
        st.subheader("No impossible avatars")


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


if __name__ == "__main__":
    last_patch = Patch.objects.last()

    dfs = [load_tourney_results(league, patch_id=last_patch.id) for league in league_to_folder.values()]

    for df, league in zip(dfs, league_to_folder.keys()):
        df["league"] = league

    compute_sus_overview(df)
