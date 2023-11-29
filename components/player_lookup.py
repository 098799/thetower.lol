import datetime
import os
from collections import defaultdict
from html import escape
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from components.util import get_options
from dtower.sus.models import SusPerson
from dtower.tourney_results.constants import (
    Graph,
    Options,
    all_relics,
    champ,
    colors_017,
    colors_018,
    league_to_folder,
    leagues,
    position_colors,
    position_stratas,
    stratas_boundaries,
    stratas_boundaries_018,
)
from dtower.tourney_results.data import get_banned_ids, get_id_lookup, get_patches, get_player_list, get_soft_banned_ids, load_tourney_results
from dtower.tourney_results.formatting import BASE_URL, color_position, html_to_rgb
from dtower.tourney_results.models import PatchNew as Patch

sus_ids = set(SusPerson.objects.filter(sus=True).values_list("player_id", flat=True))
id_mapping = get_id_lookup()


def compute_player_lookup(df, options: Options, all_leagues=False):
    if options.current_player is not None:
        all_leagues = False

    hidden_features = os.environ.get("HIDDEN_FEATURES")

    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    if not all_leagues:
        league_col, user_col = st.columns([1, 2])
    else:
        user_col = st

    league_choices = leagues
    user_choices = []

    if options.current_player is not None:
        user = options.current_player
        find_player_across_leagues(user)

        found = find_player_across_leagues(user)

        if found is not None:
            df, player_df, preselected_league = found
            league_choices = [preselected_league] + [league_choice for league_choice in leagues if league_choice != preselected_league]
            user_choices = [user]

    league = league_col.selectbox("League?", league_choices) if not all_leagues else all

    if df is None or league != preselected_league:
        limit_no_results = None

        if all_leagues:  # limit amount of results to load faster the hidden site
            user_col, checkbox_col = user_col.columns([5, 1])
            limit_loading = checkbox_col.checkbox("search last 3 months", value=True)

            if limit_loading:
                limit_no_results = 8 * 3  # 3 months-ish for now

        if not all_leagues:
            df = load_tourney_results(folder=league_to_folder[league], limit_no_results=limit_no_results)

            if league != champ:
                df["league"] = league
        else:
            dfs = [load_tourney_results(league, limit_no_results=limit_no_results) for league in leagues]

            for df, league in zip(dfs, leagues):
                df["league"] = league

            df = pd.concat(dfs)

    first_choices, all_real_names, all_tourney_names, all_user_ids, last_top_scorer = get_player_list(df)
    player_list = [""] + first_choices + sorted(all_real_names | all_tourney_names) + all_user_ids

    if not hidden_features:
        sus_nicknames = set(SusPerson.objects.filter(sus=True).values_list("name", flat=True))
        player_list = [player for player in player_list if player not in sus_ids | sus_nicknames]

    if not all_leagues:
        user = user_col.selectbox("Which user would you like to lookup?", user_choices + player_list)
    else:
        sub_user_col, id_col, tourney_name_col = user_col.columns([1, 1, 1])
        real_name = sub_user_col.selectbox("Lookup by real name", [""] + first_choices + ([name for name in all_real_names if name not in set(first_choices)]))

        id_ = None
        tourney_name = None

        if not real_name:
            id_ = id_col.selectbox("Lookup by id", [""] + sorted(all_user_ids))

            if not id_:
                tourney_name = tourney_name_col.selectbox("Lookup by tourney name", [""] + sorted(all_tourney_names))

        user = real_name or id_ or tourney_name

    # lol
    if user == "Soelent":
        st.image("towerfans.jpg")

    if not user:
        return

    info_tab, graph_tab, raw_data_tab, patch_tab = st.tabs(["Info", "Tourney performance graph", "Full results data", "Patch best"])

    if (player_df := _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user)) is None:
        st.write("User not found in this league.")
        return

    # todo should be extracted
    if len(player_df.id.unique()) >= 2:
        potential_ids = player_df.id.unique().tolist()
        aggreg = player_df.groupby("id").count()
        most_common_id = aggreg[aggreg.tourney_name == aggreg.tourney_name.max()].index[0]
        user_ids = graph_tab.multiselect(
            "Since multiple players had the same username, please choose id. If you are confident the same user used multiple ids, you can select multiple. If it's different users, data below won't make much sense",
            potential_ids,
            default=most_common_id,
        )

        if not user_ids:
            return

        player_df = df[df.id.isin(user_ids)]
    else:
        player_df = df[df.id == player_df.iloc[0].id]

    player_df = player_df.sort_values("date", ascending=False)

    draw_info_tab(info_tab, user, player_df, hidden_features)

    patches_options = sorted([patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True)
    graph_options = [options.default_graph.value] + [
        value for value in list(Graph.__members__.keys()) + patches_options if value != options.default_graph.value
    ]
    patch_col, average_col = graph_tab.columns([1, 1])
    patch = patch_col.selectbox("Limit results to a patch? (see side bar to change default)", graph_options)
    filter_bcs = patch_col.multiselect("Filter by battle conditions?", sorted({bc for bcs in df.bcs for bc in bcs}, key=lambda bc: bc.shortcut))
    rolling_average = average_col.slider("Use rolling average for results from how many tourneys?", min_value=1, max_value=10, value=5)

    colors, patch_df, stratas = handle_colors_dependant_on_patch(df, patch, player_df)

    if filter_bcs:
        sbcs = set(filter_bcs)
        patch_df = patch_df[patch_df.bcs.map(lambda table_bcs: sbcs & set(table_bcs) == sbcs)]
        player_df = player_df[player_df.bcs.map(lambda table_bcs: sbcs & set(table_bcs) == sbcs)]

    tbdf = patch_df.reset_index(drop=True)
    tbdf["average"] = tbdf.wave.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    tbdf["position_average"] = tbdf.position.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    tbdf["bcs"] = tbdf.bcs.map(lambda bc_qs: " / ".join([bc.shortcut for bc in bc_qs]))

    if len(tbdf) > 1:
        pos_col, tweak_col = graph_tab.columns([1, 1])

        graph_position_instead = pos_col.checkbox("Graph position instead")
        average_foreground = tweak_col.checkbox("Average in the foreground?", value=False)
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not graph_position_instead:
            handle_not_graph_position_instead(average_foreground, colors, fig, rolling_average, stratas, tbdf, df)
        else:
            handle_is_graph_position(average_foreground, fig, rolling_average, tbdf)

        handle_start_date_loop(fig, graph_position_instead, tbdf)
        fig.update_layout(hovermode="x unified")

        graph_tab.plotly_chart(fig)

    additional_column = ["league"] if "league" in tbdf.columns else []
    additional_format = [None] if "league" in tbdf.columns else []

    player_df["average"] = player_df.wave.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    player_df = player_df.reset_index(drop=True)
    player_df["battle"] = ["/".join([bc.shortcut for bc in bcs]) for bcs in player_df.bcs]

    def dataframe_styler(player_df):
        return (
            player_df[["name", "wave", "#", "date", "patch", "battle"] + additional_column]
            .style.apply(
                lambda row: [
                    f"color: {player_df[player_df['date']==row.date].name_role_color.iloc[0]}",
                    f"color: {player_df[player_df['date']==row.date].wave_role_color.iloc[0]}",
                    None,
                    None,
                    None,
                    None,
                ]
                + additional_format,
                axis=1,
            )
            .map(color_position, subset=["#"])
            # .bar(subset=["wave"], color="#222222", vmin=0, vmax=max(player_df.wave))
        )

    player_df = player_df.rename({"tourney_name": "name", "position": "#"}, axis=1)
    raw_data_tab.dataframe(dataframe_styler(player_df), use_container_width=True, height=800)

    small_df = player_df.loc[:9]
    info_tab.write(
        '<div style="overflow-x:auto;">' + dataframe_styler(small_df).to_html(escape=False) + "</div>",
        unsafe_allow_html=True,
    )

    write_for_each_patch(patch_tab, player_df)

    for container in [info_tab, graph_tab, raw_data_tab, patch_tab]:
        container.write(f"User id(s) used: <b>{tbdf.raw_id.unique()}</b>", unsafe_allow_html=True)


def draw_info_tab(info_tab, user, player_df, hidden_features):
    url_tab, comp_tab = info_tab.columns([3, 1])
    url_tab.code(f"http://{BASE_URL}/Player%20Lookup?" + urlencode({"player": user}, doseq=True))
    url = f"http://{BASE_URL}/Player%20Comparison?" + urlencode({"compare": user}, doseq=True)
    comp_tab.write(f"<a href='{url}'>🔗 Compare with...</a>", unsafe_allow_html=True)
    handle_sus_or_banned_ids(info_tab, player_df.iloc[0].id, sus_ids)

    real_name = player_df.iloc[0].real_name
    current_role_color = player_df.iloc[0].name_role.color

    if hidden_features:
        info_tab.write(
            f"<a href='https://admin.thetower.lol/admin/sus/susperson/add/?player_id={player_df.iloc[0].id}&name={escape(real_name)}' target='_blank'>🔗 sus me</a>",
            unsafe_allow_html=True,
        )

    avatar = player_df.iloc[0].avatar
    relic = player_df.iloc[0].relic

    avatar_string = f"<img src='./app/static/Tower_Skins/{avatar}.png' width=100>" if avatar > 0 else ""
    title = f"title='{all_relics[relic][0]}, {all_relics[relic][1]} {all_relics[relic][2]}'" if relic in all_relics else ""
    relic_string = f"<img src='./app/static/Tower_Relics/{relic}.png' width=100, {title}>" if relic >= 0 else ""

    info_tab.write(
        f"<table class='top'><tr><td>{avatar_string}</td><td><div style='font-size: 30px; color: {current_role_color}'><span style='vertical-align: middle;'>{real_name}</span></div><div style='font-size: 15px'>ID: {player_df.iloc[0].id}</div></td><td>{relic_string}</td></tr></table>",
        unsafe_allow_html=True,
    )


def write_for_each_patch(patch_tab, player_df):
    wave_data = []
    position_data = []

    for patch, patch_df in player_df.groupby("patch"):
        max_wave = patch_df.wave.max()
        max_wave_data = patch_df[patch_df.wave == max_wave].iloc[0]

        max_pos = patch_df["#"].min()
        max_pos_data = patch_df[patch_df["#"] == max_pos].iloc[0]

        wave_data.append(
            {
                "patch": f"0.{patch.version_minor}.{patch.version_patch}",
                "max_wave": max_wave,
                "tourney_name": max_wave_data.name,
                "date": max_wave_data.date,
                "patch_role_color": max_wave_data.name_role.color,
                "battle_conditions": ", ".join(max_wave_data.bcs.values_list("shortcut", flat=True)),
            }
        )

        position_data.append(
            {
                "patch": f"0.{patch.version_minor}.{patch.version_patch}",
                "max_position": max_pos,
                "tourney_name": max_pos_data.name,
                "date": max_pos_data.date,
                "max_position_color": max_pos_data.position_role_color,
                "battle_conditions": ", ".join(max_pos_data.bcs.values_list("shortcut", flat=True)),
            }
        )

    wave_df = pd.DataFrame(wave_data).sort_values("patch", ascending=False).reset_index(drop=True)
    position_df = pd.DataFrame(position_data).sort_values("patch", ascending=False).reset_index(drop=True)

    wave_tbdf = wave_df[["patch", "max_wave", "tourney_name", "date", "battle_conditions"]].style.apply(
        lambda row: [
            None,
            f"color: {wave_df[wave_df.patch == row.patch].patch_role_color.iloc[0]}",
            None,
            None,
            None,
        ],
        axis=1,
    )

    position_tbdf = position_df[["patch", "max_position", "tourney_name", "date", "battle_conditions"]].style.apply(
        lambda row: [
            None,
            f"color: {position_df[position_df.patch == row.patch].max_position_color.iloc[0]}",
            None,
            None,
            None,
        ],
        axis=1,
    )

    patch_tab.write("Best wave per patch")
    patch_tab.dataframe(wave_tbdf)

    patch_tab.write("Best position per patch")
    patch_tab.dataframe(position_tbdf)


def handle_start_date_loop(fig, graph_position_instead, tbdf):
    for index, (start, version_minor, version_patch, interim) in enumerate(
        Patch.objects.all().values_list("start_date", "version_minor", "version_patch", "interim")
    ):
        name = f"0.{version_minor}.{version_patch}"
        interim = " interim" if interim else ""

        if start < tbdf.date.min() - datetime.timedelta(days=2) or start > tbdf.date.max() + datetime.timedelta(days=3):
            continue

        fig.add_vline(x=start, line_width=3, line_dash="dash", line_color="#888", opacity=0.4)
        fig.add_annotation(
            x=start,
            y=(tbdf.position.min() + 10 * (index % 5)) if graph_position_instead else (tbdf.wave.max() - 150 * (index % 5 + 1)),
            text=f"Patch {name}{interim} start",
            showarrow=True,
            arrowhead=1,
        )


def handle_is_graph_position(average_foreground, fig, rolling_average, tbdf):
    foreground_kwargs = {}
    # background_kwargs = dict(line_dash="dot", line_color="#888", opacity=0.6)
    background_kwargs = dict(line_dash="dot", line_color="#FF4B4B", opacity=0.6)
    fig.add_trace(
        go.Scatter(
            x=tbdf.date,
            y=tbdf.position,
            name="Tourney position",
            **foreground_kwargs if not average_foreground else background_kwargs,
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=tbdf.date,
            y=tbdf.position_average,
            name=f"{rolling_average} tourney moving average",
            **foreground_kwargs if average_foreground else background_kwargs,
        ),
        secondary_y=True,
    )
    fig.update_yaxes(secondary_y=True, range=[tbdf.position.max() + 20, 0])


def handle_not_graph_position_instead(average_foreground, colors, fig, rolling_average, stratas, tbdf, df):
    tops = position_stratas[:-1][::-1]
    strata_to_color = dict(zip(tops, position_colors[2:][::-1] + ["#FFFFFF"]))

    # def guess_closest_tops(tbdf):
    #     def find_two_closest(mean_last_position, tops):
    #         for index, top in enumerate(tops):
    #             if top > mean_last_position:
    #                 return tops[index - 1], top

    #     mean_last_position = tbdf[:5].position.mean()

    #     return find_two_closest(mean_last_position, tops)

    best_position = tbdf.position.min()
    worst_position = tbdf.position.max()

    for strata in tops:
        if strata <= best_position:
            begin = strata
            break
    else:
        begin = tops[0]

    for strata in tops:
        if strata >= worst_position:
            end = strata
            break
    else:
        end = tops[-1]

    stratas_for_plot = [strata for strata in tops if strata >= begin and strata <= end]

    all_results = df[df.date.isin(tbdf.date.unique())]
    all_results = all_results[all_results.position != -1]

    min_by_strata = defaultdict(list)
    max_by_strata = defaultdict(list)

    for date, sdf in all_results.groupby("date"):
        for strata in tops:
            min_by_strata[strata].append(sdf[sdf.position <= strata].wave.min())
            max_by_strata[strata].append(sdf[sdf.position <= strata].wave.max())

    foreground_kwargs = {}
    background_kwargs = dict(line_dash="dot", line_color="#888", opacity=0.6)
    # background_kwargs = dict(line_dash="dot", line_color="#FF4B4B", opacity=0.6)
    fig.add_trace(
        go.Scatter(
            x=tbdf.date,
            y=tbdf.wave,
            name="Wave (left axis)",
            customdata=tbdf.bcs,
            hovertemplate="%{y}, BC: %{customdata}",
            marker=dict(size=7, opacity=1),
            line=dict(width=2, color="#FF4B4B"),
            **foreground_kwargs if not average_foreground else background_kwargs,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=tbdf.date,
            y=tbdf.average,
            name=f"{rolling_average} tourney moving average",
            **foreground_kwargs if average_foreground else background_kwargs,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=tbdf.date[::-1],
            y=max_by_strata[stratas_for_plot[0]],
            name=f"Max top {stratas_for_plot[0]}",
            line_dash="dot",
            marker=dict(size=0, opacity=0),
            opacity=0.6,
            line_color=html_to_rgb(strata_to_color[stratas_for_plot[0]], transparency=0.2),
        )
    )

    for strata in stratas_for_plot[1:]:
        fig.add_trace(
            go.Scatter(
                x=tbdf.date[::-1],
                y=min_by_strata[strata],
                name=f"Min top {strata}",
                line_dash="dot",
                marker=dict(size=0, opacity=0),
                opacity=0.6,
                fill="tonexty",
                line_color=html_to_rgb(strata_to_color[strata], transparency=0.2),
                fillcolor=html_to_rgb(strata_to_color[strata], transparency=0.1),
            )
        )

    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # min_ = min(tbdf.wave)
    # max_ = max(tbdf.wave)
    # for color_, strata in zip(colors, stratas):
    #     if max_ > strata > min_:
    #         fig.add_hline(y=strata, line_color=color_, line_dash="dash", opacity=0.4, line_width=3)


def handle_colors_dependant_on_patch(df, patch, player_df):
    if isinstance(patch, Patch):
        patch_df = player_df[player_df.patch == patch]

        if patch.version_minor >= 18:
            colors, stratas = colors_018, stratas_boundaries_018
        else:
            colors, stratas = colors_017, stratas_boundaries
    elif patch == Graph.last_16.value:
        patch_df = player_df[player_df.date.isin(df.date.unique()[-16:])]
        colors, stratas = colors_018, stratas_boundaries_018
    else:
        patch_df = player_df
        colors, stratas = colors_018, stratas_boundaries_018
    return colors, patch_df, stratas


def handle_sus_or_banned_ids(info_tab, id_, sus_ids):
    if id_ in get_banned_ids():
        info_tab.warning("This player is banned by the Support team.")
    if id_ in get_soft_banned_ids():
        info_tab.warning("This player is banned.")
    if id_ in sus_ids:
        info_tab.error("This player is considered sus.")


def _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user):
    if user in (set(first_choices) | all_real_names | all_tourney_names):
        player_df = df[(df.real_name == user) | (df.tourney_name == user)]
    elif user in all_user_ids:
        player_df = df[df.id == id_mapping.get(user, user)]
    else:
        player_df = None

    return player_df


def find_user(all_real_names, all_tourney_names, all_user_ids, df, first_choices, user):
    if (player_df := _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user)) is not None:
        return df, player_df
    else:
        # expensive branch, maybe we gotta look in another league? Should only happen if the user is passed as query param
        found = find_player_across_leagues(user)

        if found is None:
            raise ValueError(f"Could not find user {user}.")

        df, player_df, league = found

        return df, player_df


def find_player_across_leagues(user):
    for league in leagues:
        df = load_tourney_results(folder=league_to_folder[league])

        first_choices, all_real_names, all_tourney_names, all_user_ids, _ = get_player_list(df)

        if (player_df := _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user)) is not None:
            df["league"] = league
            return df, player_df, league


if __name__ == "__main__":
    options = get_options(links=False)
    compute_player_lookup(None, options=options, all_leagues=True)
