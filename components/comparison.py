import datetime
import os
from statistics import median, stdev
from urllib.parse import urlencode

import pandas as pd
import plotly.express as px
import streamlit as st

from components.search import compute_search
from components.util import get_options
from dtower.sus.models import KnownPlayer, PlayerId, SusPerson
from dtower.tourney_results.constants import (
    Graph,
    Options,
    all_relics,
    colors_017,
    colors_018,
    how_many_results_public_site,
    leagues,
    stratas_boundaries,
    stratas_boundaries_018,
)
from dtower.tourney_results.data import get_details, get_patches
from dtower.tourney_results.formatting import BASE_URL, color_top_18, make_player_url
from dtower.tourney_results.models import PatchNew as Patch
from dtower.tourney_results.models import TourneyRow

sus_ids = set(SusPerson.objects.filter(sus=True).values_list("player_id", flat=True))


def compute_comparison(options: Options):
    hidden_features = os.environ.get("HIDDEN_FEATURES")

    def diplay_comparison():
        st.session_state.display_comparison = True
        options.compare_players = st.session_state.get("comparison", [])
        st.session_state.counter = st.session_state.counter + 1 if st.session_state.get("counter") else 1

    def remove_from_comparison(player):
        st.session_state.comparison.remove(player)
        st.session_state.counter = st.session_state.counter + 1 if st.session_state.get("counter") else 1

    def search_for_new():
        st.session_state.pop("display_comparison", None)
        st.session_state.counter = st.session_state.counter + 1 if st.session_state.get("counter") else 1

    if (currently := st.session_state.get("comparison", [])) and st.session_state.get("display_comparison") is not True:
        st.write("Currently added:")

        for player in currently:
            addee_col, pop_col = st.columns([1, 1])

            addee_col.write(f"{st.session_state.addee_map[player]} ({player})")
            pop_col.button("Remove", on_click=remove_from_comparison, args=(player,), key=f"{player}remove")

        st.button("Show comparison", on_click=diplay_comparison, key="show_comparison_top")

    if not options.compare_players and (st.session_state.get("display_comparison") is None):
        compute_search(player=False, comparison=True)
        exit()
    else:
        users = options.compare_players or st.session_state.comparison

    search_for_new = st.button("Search for another player?", on_click=search_for_new)

    st.code(f"http://{BASE_URL}/Player%20Comparison?" + urlencode({"compare": users}, doseq=True))

    player_ids = PlayerId.objects.filter(id__in=users)
    known_players = KnownPlayer.objects.filter(ids__in=player_ids)
    all_player_ids = set(PlayerId.objects.filter(player__in=known_players).values_list("id", flat=True)) | set(users)

    hidden_query = {} if hidden_features else {"result__public": True, "position__lt": how_many_results_public_site, "position__gt": 0}
    rows = TourneyRow.objects.filter(player_id__in=all_player_ids, **hidden_query)
    rows = filter_lower_leagues(rows)

    player_df = get_details(rows)

    patches_options = sorted([patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True)
    graph_options = [options.default_graph.value] + [
        value for value in list(Graph.__members__.keys()) + patches_options if value != options.default_graph.value
    ]
    patch_col, bc_col = st.columns([1, 1])
    patch = patch_col.selectbox("Limit results to a patch? (see side bar to change default)", graph_options)
    filter_bcs = bc_col.multiselect("Filter by battle conditions?", sorted({bc for bcs in player_df.bcs for bc in bcs}, key=lambda bc: bc.shortcut))

    datas = [(sdf, real_name) for real_name, sdf in player_df.groupby("real_name") if len(sdf) >= 2]
    datas = filter_plot_datas(datas, patch, filter_bcs)

    if not datas:
        return

    datas = sorted([(data, user) for data, user in datas], key=lambda datum: max(datum[0].wave), reverse=True)

    summary = pd.DataFrame(
        [
            [
                data.real_name.unique()[0],
                user,
                len(data),
                max(data.wave),
                int(round(median(data.wave), 0)),
                int(round(stdev(data.wave), 0)),
                min(data.wave),
            ]
            for data, user in datas
        ],
        columns=["Name", "Search term", "No. tourneys", "total PB", "Median", "Stdev", "Lowest score"],
    )
    summary.set_index(keys="Name")

    if options.links_toggle:
        to_be_displayed = summary.style.format(make_player_url, subset=["Name"]).to_html(escape=False)
        st.write(to_be_displayed, unsafe_allow_html=True)
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)

    pd_datas = pd.concat([data for data, _ in datas])
    pd_datas["bcs"] = pd_datas.bcs.map(lambda bc_qs: " / ".join([bc.shortcut for bc in bc_qs]))

    last_5_tourneys = sorted(pd_datas.date.unique())[-5:][::-1]
    last_5_bcs = [pd_datas[pd_datas.date == date].bcs.iloc[0] for date in last_5_tourneys]
    last_results = pd.DataFrame(
        [
            [
                data.real_name.unique()[0],
            ]
            + [wave_serie.iloc[0] if not (wave_serie := data[data.date == date].wave).empty else 0 for date in last_5_tourneys]
            for data, _ in datas
        ],
        columns=["Name", *[f"{date.month}/{date.day}: {bc}" for date, bc in zip(last_5_tourneys, last_5_bcs)]],
    )

    last_results = last_results.style.apply(lambda row: [None, *[color_top_18(wave=row[i + 1]) for i in range(len(last_5_tourneys))]], axis=1)

    if options.links_toggle:
        to_be_displayed = last_results.format(make_player_url, subset=["Name"]).to_html(escape=False)
        st.write(to_be_displayed, unsafe_allow_html=True)
    else:
        st.dataframe(last_results, use_container_width=True, hide_index=True)

    pd_datas = pd_datas.drop_duplicates()

    fig = px.line(pd_datas, x="date", y="wave", color="real_name", markers=True, custom_data=["bcs", "position"])
    fig.update_traces(hovertemplate="%{y}<br>Postion: %{customdata[1]}<br>BC: %{customdata[0]}")
    fig.update_layout(hovermode="x unified")

    min_ = min(pd_datas.wave)
    max_ = max(pd_datas.wave)

    enrich_plot(fig, max_, min_, pd_datas)

    st.plotly_chart(fig)

    fig = px.line(pd_datas, x="date", y="position", color="real_name", markers=True)
    fig.update_yaxes(range=[max(pd_datas.position), min(pd_datas.position)])
    st.plotly_chart(fig)

    with st.expander("Debug data..."):
        data = {real_name: list(df.id.unique()) for real_name, df in pd_datas.groupby("real_name")}
        st.write("Player ids used:")
        st.json(data)


def filter_plot_datas(datas, patch, filter_bcs):
    filtered_datas = []

    for sdf, name in datas:
        patch_df = get_patch_df(sdf, sdf, patch)

        if filter_bcs:
            sbcs = set(filter_bcs)
            patch_df = patch_df[patch_df.bcs.map(lambda table_bcs: sbcs & set(table_bcs) == sbcs)]

        tbdf = patch_df.reset_index(drop=True)

        if len(tbdf) >= 2:
            filtered_datas.append((tbdf, name))

    return filtered_datas


def enrich_plot(fig, max_, min_, pd_datas):
    for index, (start, version_minor, version_patch, interim) in enumerate(
        Patch.objects.all().values_list("start_date", "version_minor", "version_patch", "interim")
    ):
        name = f"0.{version_minor}.{version_patch}"
        interim = "interim" if interim else ""

        if start < pd_datas.date.min() - datetime.timedelta(days=2) or start > pd_datas.date.max() + datetime.timedelta(days=3):
            continue

        fig.add_vline(x=start, line_width=3, line_dash="dash", line_color="#888", opacity=0.4)
        fig.add_annotation(
            x=start,
            y=pd_datas.wave.max() - 300 * (index % 2 + 1),
            text=f"Patch {name}{interim} start",
            showarrow=True,
            arrowhead=1,
        )


def handle_patch_colors(df, patch, player_df):
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


def get_patch_df(df, player_df, patch):
    if isinstance(patch, Patch):
        patch_df = player_df[player_df.patch == patch]
    elif patch == Graph.last_16.value:
        patch_df = player_df[player_df.date.isin(sorted(df.date.unique())[-16:])]
    else:
        patch_df = player_df
    return patch_df


def filter_lower_leagues(rows):
    # only leave top league results -- otherwise results are not comparable?
    leagues_in = rows.values_list("result__league", flat=True).distinct()

    for league in leagues:
        if league in leagues_in:
            break

    rows = rows.filter(result__league=league)
    return rows


if __name__ == "__main__":
    st.set_page_config(layout="centered")
    options = get_options(links=False)
    compute_comparison(options=options)
