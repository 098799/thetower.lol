import streamlit as st

from components.constants import Options, sus_ids, sus_person
from components.data import load_tourney_results
from components.formatting import am_i_sus, color_position__top, make_url, strike


def compute_tourney_results(df, options: Options):
    tourneys = sorted(df["date"].unique(), reverse=True)
    tourney_file_name = st.selectbox("Select tournament:", tourneys)

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

    if options.congrats_toggle:
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

                if current_wave > previous_best_wave:
                    new_pbs.append((current_wave, current_wave_role, current_date, previous_results[previous_results["wave"] == previous_best_wave].iloc[0]))

                if current_role > previous_best_role:
                    new_role_rows.append(person_row)
                    # new_roles.append(previous_results[previous_results["wave_role"] == previous_best_role].iloc[0])

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
                st.write(f"Congratulations for new PBs:<br>{new_wave_string}.", unsafe_allow_html=True)

    to_be_displayed = (
        to_be_displayed[["position", "tourney_name", "real_name", "wave"]]
        .style.apply(
            lambda row: [None, None, f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}", None],
            axis=1,
        )
        .apply(
            lambda row: [None, None, None, f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}"],
            axis=1,
        )
        .applymap(color_position__top, subset=["position"])
        .applymap(am_i_sus, subset=["real_name"])
    )

    if options.links_toggle:
        to_be_displayed = to_be_displayed.format(make_url, subset=["real_name"]).to_html(escape=False)
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
