import plotly.express as px
import streamlit as st

from components.util import deprecated
from dtower.tourney_results.constants import Graph, Options, how_many_results_public_site, how_many_results_public_site_other
from dtower.tourney_results.data import get_patches, get_sus_ids, load_tourney_results
from dtower.tourney_results.formatting import color_position__top, make_player_url

patches = sorted([patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True)


def compute_top(df, options: Options):
    sus_ids = get_sus_ids()

    def format_(row, df, column):
        return f"color: {df[df['ovr_pos'] == row['ovr_pos']][column].iloc[0]}"

    st.title("Top tournament scores")
    patch = st.selectbox("Patch?", patches)
    st.write("Counting only highest per person:")

    non_sus_df = df[~df["id"].isin(sus_ids)]
    patch_df = non_sus_df[non_sus_df["patch"] == patch]

    overall_df = patch_df.sort_values("wave", ascending=False).reset_index(drop=True).iloc[:how_many_results_public_site]
    overall_df["ovr_pos"] = overall_df.index + 1
    condensed_df = patch_df.sort_values("wave", ascending=False).drop_duplicates("id").reset_index(drop=True).iloc[:how_many_results_public_site_other]
    condensed_df["ovr_pos"] = condensed_df.index + 1

    condensed_tbd = (
        condensed_df[["date", "real_name", "wave", "position", "ovr_pos"]]
        .style.apply(lambda row: [None, None, format_(row=row, df=condensed_df, column="wave_role_color"), None, None], axis=1)
        .map(color_position__top, subset=["position"])
        .apply(lambda row: [None, format_(row=row, df=condensed_df, column="name_role_color"), None, None, None], axis=1)
    )

    fig = px.bar(condensed_df[:40], x="real_name", y="wave")

    try:
        fig.update_yaxes(range=[min([condensed_df.iloc[40].wave - 20, 2000]), condensed_df.iloc[0].wave + 20])
    except IndexError:
        st.warning("No data for this patch")

    st.plotly_chart(fig)

    if options.links_toggle:
        condensed_tbd = condensed_tbd.format(make_player_url, subset=["real_name"]).to_html(escape=False)
        st.write(condensed_tbd, unsafe_allow_html=True)
    else:
        st.dataframe(condensed_tbd, use_container_width=True, height=400)

    overall_tbd = (
        overall_df[["date", "real_name", "wave", "position", "ovr_pos"]]
        .style.apply(lambda row: [None, None, format_(row=row, df=overall_df, column="wave_role_color"), None, None], axis=1)
        .map(color_position__top, subset=["position"])
        .apply(lambda row: [None, format_(row=row, df=overall_df, column="name_role_color"), None, None, None], axis=1)
    )

    st.write("Overall:")

    if options.links_toggle:
        overall_tbd = overall_tbd.format(make_player_url, subset=["real_name"]).to_html(escape=False)
        st.write(overall_tbd, unsafe_allow_html=True)
    else:
        st.dataframe(overall_tbd, use_container_width=True, height=400)


def get_top_scores():
    deprecated()
    df = load_tourney_results("data")
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)
    compute_top(df, options)
