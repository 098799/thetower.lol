import streamlit as st

from dtower.tourney_results.constants import Options
from dtower.tourney_results.data import get_patches, get_sus_ids
from dtower.tourney_results.formatting import color_position__top, make_url

patches = sorted(get_patches(), key=lambda patch: patch.start_date, reverse=True)


def compute_top(df, options: Options):
    sus_ids = get_sus_ids()

    def format_(row, df, column):
        return f"color: {df[df['ovr_pos'] == row['ovr_pos']][column].iloc[0]}"

    st.title("Top tournament scores")
    patch = st.selectbox("Patch?", patches)
    st.write("Counting only highest per person:")

    non_sus_df = df[~df["id"].isin(sus_ids)]
    patch_df = non_sus_df[non_sus_df["patch"] == patch]

    overall_df = patch_df.sort_values("wave", ascending=False).reset_index(drop=True).iloc[:500]
    overall_df["ovr_pos"] = overall_df.index + 1
    condensed_df = patch_df.sort_values("wave", ascending=False).drop_duplicates("id").reset_index(drop=True).iloc[:100]
    condensed_df["ovr_pos"] = condensed_df.index + 1

    condensed_tbd = (
        condensed_df[["date", "real_name", "wave", "position", "ovr_pos"]]
        .style.apply(lambda row: [None, None, format_(row=row, df=condensed_df, column="wave_role_color"), None, None], axis=1)
        .applymap(color_position__top, subset=["position"])
        .apply(lambda row: [None, format_(row=row, df=condensed_df, column="name_role_color"), None, None, None], axis=1)
    )

    if options.links_toggle:
        condensed_tbd = condensed_tbd.format(make_url, subset=["real_name"]).to_html(escape=False)
        st.write(condensed_tbd, unsafe_allow_html=True)
    else:
        st.dataframe(condensed_tbd, use_container_width=True, height=400)

    overall_tbd = (
        overall_df[["date", "real_name", "wave", "position", "ovr_pos"]]
        .style.apply(lambda row: [None, None, format_(row=row, df=overall_df, column="wave_role_color"), None, None], axis=1)
        .applymap(color_position__top, subset=["position"])
        .apply(lambda row: [None, format_(row=row, df=overall_df, column="name_role_color"), None, None, None], axis=1)
    )

    st.write("Overall:")

    if options.links_toggle:
        overall_tbd = overall_tbd.format(make_url, subset=["real_name"]).to_html(escape=False)
        st.write(overall_tbd, unsafe_allow_html=True)
    else:
        st.dataframe(overall_tbd, use_container_width=True, height=400)
