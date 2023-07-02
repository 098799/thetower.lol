import datetime
import os
from functools import partial
from typing import Optional

import plotly.express as px
import streamlit as st
from streamlit_js_eval import get_page_location

from dtower.tourney_results.constants import Options, sus_person
from dtower.tourney_results.data import get_sus_ids
from dtower.tourney_results.formatting import am_i_sus, color_position__top, make_url, strike
from dtower.tourney_results.models import PatchNew as Patch


class Results:
    def __init__(self, df, options: Options) -> None:
        self.df = df
        self.options = options
        self.hidden_features = os.environ.get("HIDDEN_FEATURES")
        self.sus_ids = get_sus_ids()
        self.show_hist: Optional[bool] = None

    def congrats(self, filtered_df):
        if not self.hidden_features and self.congrats_toggle:
            with st.expander("Congrats! 🎉"):
                new_pbs, new_role_rows = self.handle_current_results(filtered_df)

                new_role_string = ", ".join(
                    [f"<font color='{row.wave_role.color}'>{self.df[self.df.id == row.id].iloc[0].real_name}</font>" for row in new_role_rows]
                )

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

    def handle_current_results(self, filtered_df):
        new_pbs = []
        new_role_rows = []

        for index, person_row in filtered_df.iterrows():
            if person_row.id in self.sus_ids:
                continue

            players_df = self.df[(self.df["id"] == person_row["id"]) & (
                        self.df["patch_version"] == person_row["patch_version"])].reset_index(drop=True)

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
                new_pbs.append(
                    (current_wave, current_wave_role, current_date,
                     previous_results[previous_results["wave"] == previous_best_wave].iloc[0])
                )

            if current_role > previous_best_role or len(players_df) == 1:
                new_role_rows.append(person_row)

        return new_pbs, new_role_rows

    def _hidden_time_series(self, df):
        if len(self.datetimes) > 3:
            today = st.checkbox("Overall?", value=True)

            if today:
                offset = st.slider("Offset for?", min_value=0, max_value=20, value=10)
                which_selection = st.slider("Which part of players for?", min_value=0, max_value=30, value=0)
                non_sus_df = self.df[~self.df["id"].isin(self.sus_ids)]
                patch_df = non_sus_df[non_sus_df["patch"] == Patch.objects.get(version_minor=19, beta=False)]
                top_scorers = patch_df.sort_values("wave", ascending=False).drop_duplicates("id").reset_index(drop=True)
                top_scorers = top_scorers[which_selection * offset : which_selection * offset + offset].id
                fig = px.line(self.df[self.df.id.isin(top_scorers) & self.df.date.isin(self.datetimes)], x="date", y="wave", color="real_name", markers=True)
                st.plotly_chart(fig)
            else:
                offset = st.slider("Offset?", min_value=0, max_value=20, value=10)
                which_selection = st.slider("Which part of players?", min_value=0, max_value=10, value=0)
                top_scorers = df[which_selection * offset : which_selection * offset + offset].id
                fig = px.line(self.df[self.df.id.isin(top_scorers) & self.df.date.isin(self.datetimes)], x="date", y="wave", color="real_name", markers=True)
                st.plotly_chart(fig)

    def top_of_results(self) -> str:
        unique_date_candidates = self.df["date"].unique()
        self.datetimes = [str(item) for item in unique_date_candidates if datetime.datetime.fromisoformat(str(item).rsplit(".", 1)[0]).hour]
        self.dates = [str(item).split("T")[0] for item in unique_date_candidates if not datetime.datetime.fromisoformat(str(item).rsplit(".", 1)[0]).hour]

        tourneys = sorted(self.datetimes + self.dates, reverse=True)

        tourney_col, self.results_col, debug_col = st.columns([3, 2, 1])
        tourney_file_name = tourney_col.selectbox("Select tournament:", tourneys)

        self.show_hist = debug_col.checkbox("Hist. data?", value=False)
        self.congrats_toggle = debug_col.checkbox("Congrats?", value=False)

        return tourney_file_name

    def prepare_data(self, filtered_df, how_many: int):
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
        to_be_displayed["real_name"] = [sus_person if id_ in self.sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.real_name)]
        to_be_displayed["tourney_name"] = [strike(name) if id_ in self.sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.tourney_name)]

        if not self.hidden_features:
            to_be_displayed = to_be_displayed[to_be_displayed.real_name != sus_person]

        to_be_displayed = to_be_displayed.iloc[:how_many].reset_index(drop=True)

        return to_be_displayed

    def show_hist_preparation(self, to_be_displayed, filtered_df, date: str):
        to_be_displayed = to_be_displayed[["id", "position", "tourney_name", "real_name", "wave"]]
        to_be_displayed = to_be_displayed.rename({"wave": date}, axis=1)

        common_data = self.dates + self.datetimes

        current_date_index = common_data.index(date)
        previous_4_dates = common_data[current_date_index - 4 : current_date_index][::-1]

        prev_dfs = {date: self.df[self.df["date"] == date].reset_index(drop=True) for date in previous_4_dates}

        for date_iter, prev_df in prev_dfs.items():
            to_be_displayed[date_iter] = [mini_df.iloc[0].wave if not (mini_df := prev_df[prev_df.id == id_]).empty else 0 for id_ in to_be_displayed.id]

        to_be_displayed = (
            to_be_displayed[["position", "tourney_name", "real_name", *[date, *previous_4_dates], "id"]]
            .style.apply(
                lambda row: [
                    None,
                    None,
                    f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}",
                    f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}",
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

        return to_be_displayed

    def regular_preparation(self, to_be_displayed, filtered_df):
        if self.hidden_features:
            to_be_displayed = (
                to_be_displayed[["position", "tourney_name", "real_name", "wave", "id"]]
                .style.apply(
                    lambda row: [
                        None,
                        f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}",
                        None,
                        f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}",
                        None,
                    ],
                    axis=1,
                )
                .applymap(color_position__top, subset=["position"])
                .applymap(am_i_sus, subset=["real_name"])
            )
        else:
            to_be_displayed = (
                to_be_displayed[["position", "tourney_name", "real_name", "wave"]]
                .style.apply(
                    lambda row: [
                        None,
                        f"color: {filtered_df[filtered_df['position']==row.position].name_role_color.iloc[0]}",
                        None,
                        f"color: {filtered_df[filtered_df['position']==row.position].wave_role_color.iloc[0]}",
                    ],
                    axis=1,
                )
                .applymap(color_position__top, subset=["position"])
                .applymap(am_i_sus, subset=["real_name"])
            )

        return to_be_displayed

    def compute_results(self) -> None:
        date = self.top_of_results()

        filtered_df = self.df[self.df["date"] == date].reset_index(drop=True)
        prefilter_results = self.results_col.slider("Show how many results?", min_value=50, max_value=len(filtered_df), value=100, step=50)

        to_be_displayed = self.prepare_data(filtered_df, how_many=prefilter_results)

        if self.hidden_features:
            self._hidden_time_series(to_be_displayed)

        self.congrats(filtered_df)

        if self.show_hist:
            to_be_displayed_styler = self.show_hist_preparation(to_be_displayed, filtered_df, date)
        else:
            to_be_displayed_styler = self.regular_preparation(to_be_displayed, filtered_df)

        if self.options.links_toggle:
            try:
                page_location_data = get_page_location()
                base_url = page_location_data["host"]
            except Exception:
                base_url = "thetower.lol"

            to_be_displayed_styler = to_be_displayed_styler.format(partial(make_url, base_url=base_url), subset=["real_name"]).to_html(escape=False)
            st.write(to_be_displayed_styler, unsafe_allow_html=True)
        else:
            st.dataframe(to_be_displayed_styler, use_container_width=True, height=800)


def compute_results(df, options: Options):
    Results(df, options).compute_results()


# import cProfile
# import pstats

# df = load_tourney_results("data")
# pr = cProfile.Profile()
# pr.run("compute_tourney_results(df, Options(links_toggle=False))")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
