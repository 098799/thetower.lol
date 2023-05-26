import datetime
import os
from functools import partial

import plotly.express as px
import streamlit as st
from streamlit_js_eval import get_page_location

from dtower.tourney_results.constants import Options, sus_person
from dtower.tourney_results.data import get_sus_ids
from dtower.tourney_results.formatting import am_i_sus, color_position__top, make_url, strike
from dtower.tourney_results.models import PatchNew as Patch


def compute_results(df, options: Options):
    hidden_features = os.environ.get("HIDDEN_FEATURES")

    unique_date_candidates = df["date"].unique()
    datetimes = [str(item) for item in unique_date_candidates if datetime.datetime.fromisoformat(str(item).rsplit(".", 1)[0]).hour]
    dates = [str(item).split("T")[0] for item in unique_date_candidates if not datetime.datetime.fromisoformat(str(item).rsplit(".", 1)[0]).hour]

    tourneys = sorted(datetimes + dates, reverse=True)
    sus_ids = get_sus_ids()

    tourney_col, debug_col = st.columns([5, 1])
    tourney_file_name = tourney_col.selectbox("Select tournament:", tourneys)
    show_hist = debug_col.checkbox("Historical data?", value=False)

    filtered_df = df[df["date"] == tourney_file_name].reset_index(drop=True)
    filtered_df.loc[filtered_df[filtered_df.position == 1].index[0], "real_name"] = (
        filtered_df.loc[filtered_df[filtered_df.position == 1].index[0], "real_name"] + " 🥇"
    )
    filtered_df.loc[filtered_df[filtered_df.position == 2].index[0], "real_name"] = (
        filtered_df.loc[filtered_df[filtered_df.position == 2].index[0], "real_name"] + " 🥈"
    )
    filtered_df.loc[filtered_df[filtered_df.position == 3].index[0], "real_name"] = (
        filtered_df.loc[filtered_df[filtered_df.position == 3].index[0], "real_name"] + " 🥉"
    )

    to_be_displayed = filtered_df.copy()
    to_be_displayed["real_name"] = [sus_person if id_ in sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.real_name)]
    to_be_displayed["tourney_name"] = [strike(name) if id_ in sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.tourney_name)]

    if hidden_features:
        if len(datetimes) > 3:
            today = st.checkbox("Overall?", value=True)

            if today:
                offset = st.slider("Offset for?", min_value=0, max_value=20, value=10)
                which_selection = st.slider("Which part of players for?", min_value=0, max_value=30, value=0)
                non_sus_df = df[~df["id"].isin(sus_ids)]
                patch_df = non_sus_df[non_sus_df["patch"] == Patch.objects.get(version_minor=18)]
                top_scorers = patch_df.sort_values("wave", ascending=False).drop_duplicates("id").reset_index(drop=True)
                top_scorers = top_scorers[which_selection * offset : which_selection * offset + offset].id
                fig = px.line(df[df.id.isin(top_scorers) & df.date.isin(datetimes)], x="date", y="wave", color="real_name", markers=True)
                st.plotly_chart(fig)
            else:
                offset = st.slider("Offset?", min_value=0, max_value=20, value=10)
                which_selection = st.slider("Which part of players?", min_value=0, max_value=10, value=0)
                top_scorers = to_be_displayed[which_selection * offset : which_selection * offset + offset].id
                fig = px.line(df[df.id.isin(top_scorers) & df.date.isin(datetimes)], x="date", y="wave", color="real_name", markers=True)
                st.plotly_chart(fig)

    if not hidden_features and options.congrats_toggle:
        new_role_rows = []
        new_pbs = []

        with st.expander("Congrats! 🎉"):
            for index, person_row in filtered_df.iterrows():
                if person_row.id in sus_ids:
                    continue

                players_df = df[(df["id"] == person_row["id"]) & (df["patch_version"] == person_row["patch_version"])].reset_index(drop=True)

                current_date = person_row.date
                current_wave = person_row.wave
                current_role = person_row.name_role
                current_wave_role = person_row.wave_role

                previous_results = players_df[players_df["date"] < person_row["date"]]

                if previous_results.empty:
                    continue

                previous_best_wave = previous_results.wave.max()
                previous_best_role = previous_results.wave_role.max()

                if current_wave > previous_best_wave or len(players_df) == 1:
                    new_pbs.append((current_wave, current_wave_role, current_date, previous_results[previous_results["wave"] == previous_best_wave].iloc[0]))

                if current_role > previous_best_role or len(players_df) == 1:
                    new_role_rows.append(person_row)

            new_role_string = ", ".join([f"<font color='{row.wave_role.color}'>{df[df.id == row.id].iloc[0].real_name}</font>" for row in new_role_rows])

            if new_role_string:
                st.write(f"Congratulations for new role colors {new_role_string}.", unsafe_allow_html=True)

            new_wave_string = "<br>".join(
                [
                    f"<font color='{prev_result.name_role.color}'>{prev_result.real_name}</font> pb of <b><font color='{current_wave_role.color}'>{current_wave}</font></b> by {current_wave-prev_result.wave} wave{'s' if current_wave-prev_result.wave>1 else ''} for which they waited {(current_date - prev_result.date).days} days."
                    for current_wave, current_wave_role, current_date, prev_result in new_pbs
                ]
            )

            if new_wave_string:
                st.write(f"Congratulations for new PBs:<br>{new_wave_string}", unsafe_allow_html=True)

    if not hidden_features:
        to_be_displayed = to_be_displayed[to_be_displayed.real_name != sus_person]

    if show_hist:
        to_be_displayed = to_be_displayed[["id", "position", "tourney_name", "real_name", "wave"]]
        to_be_displayed = to_be_displayed.rename({"wave": tourney_file_name}, axis=1)

        common_data = dates + datetimes

        current_date_index = common_data.index(tourney_file_name)
        previous_4_dates = common_data[current_date_index - 4 : current_date_index][::-1]

        prev_dfs = {date: df[df["date"] == date].reset_index(drop=True) for date in previous_4_dates}

        for date, prev_df in prev_dfs.items():
            to_be_displayed[date] = [mini_df.iloc[0].wave if not (mini_df := prev_df[prev_df.id == id_]).empty else 0 for id_ in to_be_displayed.id]

        to_be_displayed = (
            to_be_displayed[["position", "tourney_name", "real_name", *[tourney_file_name, *previous_4_dates], "id"]]
            .style.apply(
                lambda row: [
                    None,
                    None,
                    f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}",
                    *([None] * (len(previous_4_dates) + 2)),
                ],
                axis=1,
            )
            .apply(
                lambda row: [
                    None,
                    None,
                    None,
                    f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}",
                    *([None] * (len(previous_4_dates) + 1)),
                ],
                axis=1,
            )
            .apply(
                lambda row: [
                    *([None] * 4),
                    *[
                        f"color: {mini_df.wave_role_color.iloc[0] if not (mini_df := prev_df[prev_df.id==row.id]).empty else '#FFF'}"
                        for prev_df in prev_dfs.values()
                    ],
                    None,
                ],
                axis=1,
            )
            .applymap(color_position__top, subset=["position"])
            .applymap(am_i_sus, subset=["real_name"])
        )
    else:
        if hidden_features:
            to_be_displayed = (
                to_be_displayed[["position", "tourney_name", "real_name", "wave", "id"]]
                .style.apply(
                    lambda row: [None, f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}", None, None, None], axis=1
                )
                .apply(lambda row: [None, None, None, f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}", None], axis=1)
                .applymap(color_position__top, subset=["position"])
                .applymap(am_i_sus, subset=["real_name"])
            )
        else:
            to_be_displayed = (
                to_be_displayed[["position", "tourney_name", "real_name", "wave"]]
                .style.apply(lambda row: [None, f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}", None, None], axis=1)
                .apply(lambda row: [None, None, None, f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}"], axis=1)
                .applymap(color_position__top, subset=["position"])
                .applymap(am_i_sus, subset=["real_name"])
            )

    if options.links_toggle:
        try:
            page_location_data = get_page_location()
            base_url = page_location_data["host"]
        except Exception:
            base_url = "thetower.lol"

        to_be_displayed = to_be_displayed.format(partial(make_url, base_url=base_url), subset=["real_name"]).to_html(escape=False)
        st.write(to_be_displayed, unsafe_allow_html=True)
    else:
        st.dataframe(to_be_displayed, use_container_width=True, height=800)


# import cProfile
# import pstats

# df = load_tourney_results("data")
# pr = cProfile.Profile()
# pr.run("compute_tourney_results(df, Options(congrats_toggle=True, links_toggle=False))")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
