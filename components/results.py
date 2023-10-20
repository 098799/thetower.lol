import datetime
import os
from functools import partial
from typing import Optional

import plotly.express as px
import streamlit as st
from streamlit_js_eval import get_page_location

from components.util import links_toggle
from dtower.tourney_results.constants import Graph, Options, all_relics, champ, league_to_folder, sus_person
from dtower.tourney_results.data import get_sus_ids, load_tourney_results
from dtower.tourney_results.formatting import am_i_sus, color_position__top, make_player_url, strike
from dtower.tourney_results.models import PatchNew as Patch


class Results:
    def __init__(self, df, options: Options, league: Optional[str] = None) -> None:
        self.df = df
        self.league = league
        self.options = options
        self.hidden_features = os.environ.get("HIDDEN_FEATURES")
        self.sus_ids = get_sus_ids()
        self.show_hist: Optional[bool] = None
        self.congrats_toggle = False

    def _make_sus_link(self, id, name):
        return f"<a href='http://admin.thetower.lol/admin/sus/susperson/add/?player_id={id}&name={name}' target='_blank'>🔗 sus</a>"

    def _styler(self):
        with open("style.css", "r") as infile:
            table_styling = f"<style>{infile.read()}</style>"

        with open("funny.css", "r") as infile:
            funny_styling = f"<style>{infile.read()}</style>"

        st.write(table_styling, unsafe_allow_html=True)
        st.write(funny_styling, unsafe_allow_html=True)

    def congrats(self, filtered_df):
        if not self.hidden_features and self.congrats_toggle:
            with st.expander("Congrats! 🎉"):
                new_pbs, new_role_rows = self.populate_pbs(filtered_df)

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

    def populate_pbs(self, filtered_df):
        new_pbs = []
        new_role_rows = []

        for index, person_row in filtered_df.iterrows():
            if person_row.id in self.sus_ids:
                continue

            players_df = self.df[(self.df["id"] == person_row["id"]) & (self.df["patch"] == person_row["patch"])].reset_index(drop=True)

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
                    (
                        current_wave,
                        current_wave_role,
                        current_date,
                        previous_results[previous_results["wave"] == previous_best_wave].iloc[0],
                    )
                )

            if current_role > previous_best_role or len(players_df) == 1:
                new_role_rows.append(person_row)

        return new_pbs, new_role_rows

    def top_of_results(self) -> str:
        patch_col, tourney_col, self.results_col, self.results_col_page, debug_col = st.columns([1.0, 2, 1, 1.2, 1])

        patch = patch_col.selectbox("Patch:", Patch.objects.all().order_by("-start_date"), index=0)
        self.df = load_tourney_results(league_to_folder[self.league], patch_id=patch.id)

        self.show_hist = debug_col.checkbox("Hist data", value=False)

        date_to_bc = dict(zip(self.df.date, self.df.bcs))
        self.dates = self.df["date"].unique()
        tourneys = sorted(self.dates, reverse=True)
        tourney_titles = [date if not date_to_bc[date] else f"{date}: {', '.join(item.shortcut for item in date_to_bc[date])}" for date in tourneys]
        tourney_title = tourney_col.selectbox("Select tournament:", tourney_titles)

        if not self.hidden_features:
            self.congrats_toggle = debug_col.checkbox("Congrats", value=False)

        chosen_tourney = tourneys[tourney_titles.index(tourney_title)]

        if bcs := date_to_bc[chosen_tourney]:
            st.write(f"Battle Conditions: {', '.join(item.name for item in bcs)}")

        return chosen_tourney

    def prepare_data(self, filtered_df, current_page: int, step: int):
        begin = (current_page - 1) * step
        end = current_page * step

        to_be_displayed = filtered_df.iloc[begin:end].reset_index(drop=True)

        if not self.hidden_features:
            to_be_displayed = to_be_displayed[~to_be_displayed.id.isin(get_sus_ids())].reset_index(drop=True)

        if current_page == 1:
            for position, medal in zip([1, 2, 3], [" 🥇", " 🥈", " 🥉"]):
                if not to_be_displayed[to_be_displayed.position == position].empty:
                    to_be_displayed.loc[to_be_displayed[to_be_displayed.position == position].index[0], "real_name"] = (
                        to_be_displayed.loc[to_be_displayed[to_be_displayed.position == position].index[0], "real_name"] + medal
                    )

        to_be_displayed["real_name"] = [sus_person if id_ in self.sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.real_name)]
        to_be_displayed["tourney_name"] = [strike(name) if id_ in self.sus_ids else name for id_, name in zip(to_be_displayed.id, to_be_displayed.tourney_name)]
        to_be_displayed["avatar"] = to_be_displayed.avatar.map(
            lambda avatar_id: f"<img src='./app/static/Tower_Skins/{avatar_id}.png' width='32'>" if avatar_id != -1 else ""
        )
        to_be_displayed["relic"] = to_be_displayed.relic.map(
            lambda relic_id: (
                f"<img src='./app/static/Tower_Relics/{relic_id}.png' width='32' title='{all_relics[relic_id][0]}, {all_relics[relic_id][1]} {all_relics[relic_id][2]}'>"
            )
            if relic_id != -1 and relic_id in all_relics
            else ""
        )

        return to_be_displayed.rename(columns={"position": "#", "verified": "✓", "avatar": "⬡"})

    def show_hist_preparation(self, to_be_displayed, filtered_df, date: str):
        to_be_displayed = to_be_displayed[["id", "#", "tourney_name", "real_name", "wave", "✓"]]
        to_be_displayed = to_be_displayed.rename({"wave": date}, axis=1)

        common_data = list(self.dates)

        current_date_index = common_data.index(date)
        previous_4_dates = common_data[current_date_index - 4 : current_date_index][::-1]

        prev_dfs = {date: self.df[self.df["date"] == date].reset_index(drop=True) for date in previous_4_dates}

        for date_iter, prev_df in prev_dfs.items():
            to_be_displayed[date_iter] = [mini_df.iloc[0].wave if not (mini_df := prev_df[prev_df.id == id_]).empty else 0 for id_ in to_be_displayed.id]

        indices = ["#", "tourney_name", "real_name", *[date, *previous_4_dates], "✓", "id"]

        if self.hidden_features:
            to_be_displayed["sus_me"] = [self._make_sus_link(id, name) for id, name in zip(to_be_displayed.id, to_be_displayed.tourney_name)]
            indices += ["sus_me"]

        to_be_displayed = (
            to_be_displayed[indices]
            .style.apply(
                lambda row: [
                    None,
                    None,
                    f"color: {filtered_df[filtered_df['position']==row['#']].name_role_color.iloc[0]}",
                    f"color: {filtered_df[filtered_df['position']==row['#']].wave_role_color.iloc[0]}",
                    *[
                        f"color: {mini_df.wave_role_color.iloc[0] if not (mini_df := prev_df[prev_df.id==row.id]).empty else '#FFF'}"
                        for prev_df in prev_dfs.values()
                    ],
                    None,
                    None,
                ],
                axis=1,
            )
            .applymap(color_position__top, subset=["#"])
            .applymap(am_i_sus, subset=["real_name"])
        )

        return to_be_displayed

    def regular_preparation(self, to_be_displayed, filtered_df):
        indices = ["#", "⬡", "tourney_name", "real_name", "relic", "wave", "✓"]
        styling = lambda row: [
            None,
            None,
            None,  # f"color: {filtered_df[filtered_df['position']==row['#']].name_role_color.iloc[0]}",
            None,
            None,
            f"color: {filtered_df[filtered_df['position']==row['#']].wave_role_color.iloc[0]}",
            None,
        ]

        if self.hidden_features:
            indices += ["id", "sus_me"]
            styling = lambda row: [
                None,
                None,
                None,  # f"color: {filtered_df[filtered_df['position']==row['#']].name_role_color.iloc[0]}",
                None,
                None,
                f"color: {filtered_df[filtered_df['position']==row['#']].wave_role_color.iloc[0]}",
                None,
                None,
                None,
            ]

        if self.hidden_features:
            to_be_displayed["sus_me"] = [self._make_sus_link(id, name) for id, name in zip(to_be_displayed.id, to_be_displayed.tourney_name)]

        to_be_displayed = (
            to_be_displayed[indices].style.apply(styling, axis=1).applymap(color_position__top, subset=["#"]).applymap(am_i_sus, subset=["real_name"])
        )

        return to_be_displayed

    def compute_results(self) -> None:
        date = self.top_of_results()

        filtered_df = self.df[self.df["date"] == date].reset_index(drop=True)

        step = 100
        total_results = len(filtered_df)

        step = self.results_col_page.number_input("Results per page", min_value=100, max_value=max(total_results, 100), step=100)
        total_pages = total_results // step if total_results // step == total_results / step else total_results // step + 1
        current_page = self.results_col.number_input("Page", min_value=1, max_value=total_pages, step=1)
        to_be_displayed = self.prepare_data(filtered_df, current_page=current_page, step=step)

        self.congrats(to_be_displayed)

        if self.show_hist:
            to_be_displayed_styler = self.show_hist_preparation(to_be_displayed, filtered_df, date)
        else:
            self._styler()
            to_be_displayed_styler = self.regular_preparation(to_be_displayed, filtered_df)

        to_be_displayed_styler = to_be_displayed_styler.format(make_player_url, subset=["real_name"]).hide(axis="index").to_html(escape=False)
        st.write(to_be_displayed_styler, unsafe_allow_html=True)


def compute_results(df, options: Options, league: Optional[str] = None):
    Results(df, options, league=league).compute_results()


if __name__ == "__main__":
    options = Options(links_toggle=True, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[champ], patch_id=Patch.objects.last().id)
    compute_results(df, options, league=champ)


# import cProfile
# import pstats

# df = load_tourney_results("data")
# pr = cProfile.Profile()
# pr.run("compute_tourney_results(df, Options(links_toggle=False))")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
