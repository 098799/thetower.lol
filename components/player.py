import datetime
import os
from html import escape
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from cachetools.func import ttl_cache
from natsort import natsorted
from plotly.subplots import make_subplots

from components.search import compute_search
from components.util import get_options
from dtower.sus.models import PlayerId, SusPerson
from dtower.tourney_results.constants import (
    Graph,
    all_relics,
    colors_017,
    colors_018,
    how_many_results_public_site,
    league_to_folder,
    leagues,
    stratas_boundaries,
    stratas_boundaries_018,
)
from dtower.tourney_results.data import (
    get_banned_ids,
    get_details,
    get_id_lookup,
    get_patches,
    get_player_list,
    get_soft_banned_ids,
    load_tourney_results,
)
from dtower.tourney_results.formatting import BASE_URL, color_position
from dtower.tourney_results.models import PatchNew as Patch
from dtower.tourney_results.models import TourneyRow

sus_ids = set(SusPerson.objects.filter(sus=True).values_list("player_id", flat=True))
id_mapping = get_id_lookup()


@ttl_cache(maxsize=1000, ttl=6000)
def get_stones(player_id):
    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Origin": "https://thetower.xsollasitebuilder.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://thetower.xsollasitebuilder.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Priority": "u=0",
    }

    json_data = {
        "settings": {
            "projectId": 264652,
            "merchantId": 706526,
        },
        "loginId": "11f7ad60-c267-4747-9a0d-7613e9711fe5",
        "webhookUrl": "https://nowebhook.com",
        "user": {
            "id": player_id,
            "country": "CH",
        },
        "isUserIdFromWebhook": False,
    }

    response = requests.post("https://sb-user-id-service.xsolla.com/api/v1/user-id", headers=headers, json=json_data)

    print(response.json())

    token = response.json()["token"]

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Authorization": f"Bearer {token}",
        "Origin": "https://thetower.xsollasitebuilder.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://thetower.xsollasitebuilder.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    params = {
        "locale": "en",
        "offset": "0",
    }

    response = requests.get(
        "https://store.xsolla.com/api/v2/project/264652/items/virtual_items/group/featured",
        params=params,
        headers=headers,
    )
    print(response.json())

    return response.json()


def xsolla_things(player_id, hidden_features, info_tab):
    stone_info = get_stones(player_id)
    available = stone_info["items"][1]["limits"]["per_user"]["available"]

    if hidden_features:
        info_tab.write(f"<img src='./app/static/stones.webp' width='20px'>: {available}/5 available.", unsafe_allow_html=True)

    if available and not hidden_features:
        html_code = f"""
        <button id="combinedButton" style="padding: 10px 20px; font-size: 16px; background-color: #FF4B4B; color: white; border: none; border-radius: 5px; cursor: pointer;">Gift stone packs on xsolla!</button>

        <script>
            document.getElementById('combinedButton').addEventListener('click', async function() {{
                try {{
                    // Request to get the token
                    const tokenResponse = await fetch('https://sb-user-id-service.xsolla.com/api/v1/user-id', {{
                        method: 'POST',
                        headers: {{
                            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "en-US,en;q=0.5",
                            "Content-Type": "application/json",
                            "Origin": "https://thetower.xsollasitebuilder.com",
                            "DNT": "1",
                            "Connection": "keep-alive",
                            "Referer": "https://thetower.xsollasitebuilder.com/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "cross-site",
                            "Priority": "u=0"
                        }},
                        body: JSON.stringify({{
                            "settings": {{
                                "projectId": 264652,
                                "merchantId": 706526,
                            }},
                            "loginId": "11f7ad60-c267-4747-9a0d-7613e9711fe5",
                            "webhookUrl": "https://nowebhook.com",
                            "user": {{
                                "id": "{player_id}",
                                "country": "CH",
                            }},
                            "isUserIdFromWebhook": false,
                        }})
                    }});

                    if (!tokenResponse.ok) {{
                        throw new Error('Network response was not ok');
                    }}

                    const tokenData = await tokenResponse.json();
                    const token = tokenData.token;

                    // Open the new page with the token
                    window.open(`https://thetower.xsollasitebuilder.com/?token=${{token}}`, '_blank');

                }} catch (error) {{
                    console.error('There was a problem:', error);
                }}
            }});
        </script>
        """

        components.html(html_code, height=50)


def compute_player_lookup():
    options = get_options(links=False)
    hidden_features = os.environ.get("HIDDEN_FEATURES")

    def search_for_new():
        if "player_id" in st.session_state:
            st.session_state.pop("player_id")

    with open("style.css", "r") as infile:
        table_styling = f"<style>{infile.read()}</style>"

    st.write(table_styling, unsafe_allow_html=True)

    if player_id := st.session_state.get("player_id"):
        options.current_player = player_id

    if options.current_player is not None:
        st.button("Search for another player?", on_click=search_for_new)

    if options.current_player is None:
        compute_search(player=True, comparison=False)
        exit()

    info_tab, graph_tab, raw_data_tab, patch_tab = st.tabs(["Info", "Tourney performance graph", "Full results data", "Patch best"])

    player_ids = PlayerId.objects.filter(id=options.current_player)
    print(f"{player_ids=} {options.current_player=}")

    hidden_query = {} if hidden_features else {"result__public": True, "position__lt": how_many_results_public_site, "position__gt": 0}

    if player_ids:
        player_id = player_ids[0]
        print(f"{player_ids=} {player_id=}")
        rows = TourneyRow.objects.filter(
            player_id__in=player_id.player.ids.all().values_list("id", flat=True),
            **hidden_query,
        )
    else:
        print(f"{player_id=} {options.current_player=}")
        player_id = options.current_player
        rows = TourneyRow.objects.filter(
            player_id=player_id,
            **hidden_query,
        )

    if not rows:
        st.error(f"No results found for the player {player_id}.")
        return

    player_df = get_details(rows)

    if player_df.empty:
        st.error(f"No results found for the player {player_id}.")
        return

    player_df = player_df.sort_values("date", ascending=False)
    user = player_df["real_name"][0]

    draw_info_tab(info_tab, user, player_id, player_df, hidden_features)

    patches_options = sorted([patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True)
    graph_options = [options.default_graph.value] + [
        value for value in list(Graph.__members__.keys()) + patches_options if value != options.default_graph.value
    ]
    patch_col, average_col = graph_tab.columns([1, 1])
    patch = patch_col.selectbox("Limit results to a patch? (see side bar to change default)", graph_options)
    filter_bcs = patch_col.multiselect("Filter by battle conditions?", sorted({bc for bcs in player_df.bcs for bc in bcs}, key=lambda bc: bc.shortcut))
    rolling_average = average_col.slider("Use rolling average for results from how many tourneys?", min_value=1, max_value=10, value=5)

    colors, patch_df, stratas = handle_colors_dependant_on_patch(patch, player_df)

    if filter_bcs:
        sbcs = set(filter_bcs)
        patch_df = patch_df[patch_df.bcs.map(lambda table_bcs: sbcs & set(table_bcs) == sbcs)]
        player_df = player_df[player_df.bcs.map(lambda table_bcs: sbcs & set(table_bcs) == sbcs)]

    tbdf = patch_df.reset_index(drop=True)
    tbdf = filter_lower_leagues(tbdf)
    tbdf["average"] = tbdf.wave.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    tbdf["position_average"] = tbdf.position.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    tbdf["bcs"] = tbdf.bcs.map(lambda bc_qs: " / ".join([bc.shortcut for bc in bc_qs]))

    if len(tbdf) > 1:
        pos_col, tweak_col = graph_tab.columns([1, 1])

        graph_position_instead = pos_col.checkbox("Graph position instead")
        average_foreground = tweak_col.checkbox("Average in the foreground?", value=False)
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not graph_position_instead:
            handle_not_graph_position_instead(average_foreground, colors, fig, rolling_average, stratas, tbdf)
        else:
            handle_is_graph_position(average_foreground, fig, rolling_average, tbdf)

        handle_start_date_loop(fig, graph_position_instead, tbdf)
        fig.update_layout(hovermode="x unified")

        graph_tab.plotly_chart(fig)

    additional_column = ["league"] if "league" in tbdf.columns else []
    additional_format = [None] if "league" in tbdf.columns else []

    player_df["average"] = player_df.wave.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    player_df = player_df.reset_index(drop=True)
    player_df["battle"] = [" / ".join([bc.shortcut for bc in bcs]) for bcs in player_df.bcs]

    def dataframe_styler(player_df):
        return (
            player_df[["name", "wave", "#", "date", "patch", "battle"] + additional_column]
            .style.apply(
                lambda row: [
                    None,
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
        )

    player_df = player_df.rename({"tourney_name": "name", "position": "#"}, axis=1)
    raw_data_tab.dataframe(dataframe_styler(player_df), use_container_width=True, height=800)

    small_df = player_df.loc[:9]
    info_tab.write(
        '<div style="overflow-x:auto;">' + dataframe_styler(small_df).to_html(escape=False) + "</div>",
        unsafe_allow_html=True,
    )

    write_for_each_patch(patch_tab, player_df)

    player_id = player_df.iloc[0].id

    if player_id != "9D24669E32746D27":  # please don't buy me stones
        xsolla_things(player_id, hidden_features, info_tab)


def filter_lower_leagues(df):
    leagues_in = set(df.league)

    for league in leagues:
        if league in leagues_in:
            break

    df = df[df.league == league]
    return df


def draw_info_tab(info_tab, user, player_id, player_df, hidden_features):
    url_tab, comp_tab = info_tab.columns([3, 1])
    url_tab.code(f"http://{BASE_URL}/player?" + urlencode({"player": player_id}, doseq=True))
    # url = f"http://{BASE_URL}/Player?" + urlencode({"compare": user}, doseq=True)
    # comp_tab.write(f"<a href='{url}'>🔗 Compare with...</a>", unsafe_allow_html=True)
    handle_sus_or_banned_ids(info_tab, player_df.iloc[0].id, sus_ids)

    real_name = player_df.iloc[0].real_name
    # current_role_color = player_df.iloc[0].name_role.color

    if hidden_features:
        info_tab.write(
            f"<a href='https://admin.thetower.lol/admin/sus/susperson/add/?player_id={player_df.iloc[0].id}&name={escape(real_name)}' target='_blank'>🔗 sus me</a>",
            unsafe_allow_html=True,
        )

    avatar = player_df.iloc[0].avatar
    relic = player_df.iloc[0].relic

    if avatar in [35, 36, 39, 42, 44, 45, 46]:
        extension = "webp"
    else:
        extension = "png"

    avatar_string = f"<img src='./app/static/Tower_Skins/{avatar}.{extension}' width=100>" if avatar > 0 else ""
    title = f"title='{all_relics[relic][0]}, {all_relics[relic][1]} {all_relics[relic][2]}'" if relic in all_relics else ""

    if relic in [48, 49, 50, 51, 52, 53, 60, 61]:
        extension = "webp"
    else:
        extension = "png"

    relic_string = f"<img src='./app/static/Tower_Relics/{relic}.{extension}' width=100, {title}>" if relic >= 0 else ""

    info_tab.write(
        f"<table class='top'><tr><td>{avatar_string}</td><td><div style='font-size: 30px'><span style='vertical-align: middle;'>{real_name}</span></div><div style='font-size: 15px'>ID: {player_df.iloc[0].id}</div></td><td>{relic_string}</td></tr></table>",
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
                "tourney_name": max_wave_data["name"],
                "date": max_wave_data.date,
                # "patch_role_color": max_wave_data.name_role.color,
                "battle_conditions": ", ".join(max_wave_data.bcs.values_list("shortcut", flat=True)),
            }
        )

        position_data.append(
            {
                "patch": f"0.{patch.version_minor}.{patch.version_patch}",
                "max_position": max_pos,
                "tourney_name": max_pos_data["name"],
                "date": max_pos_data.date,
                # "max_position_color": max_pos_data.position_role_color,
                "battle_conditions": ", ".join(max_pos_data.bcs.values_list("shortcut", flat=True)),
            }
        )

    wave_data = natsorted(wave_data, key=lambda x: x["patch"], reverse=True)
    position_data = natsorted(position_data, key=lambda x: x["patch"], reverse=True)

    wave_df = pd.DataFrame(wave_data).reset_index(drop=True)
    position_df = pd.DataFrame(position_data).reset_index(drop=True)

    wave_tbdf = wave_df[["patch", "max_wave", "tourney_name", "date", "battle_conditions"]].style.apply(
        lambda row: [
            None,
            None,
            # f"color: {wave_df[wave_df.patch == row.patch].patch_role_color.iloc[0]}",
            None,
            None,
            None,
        ],
        axis=1,
    )

    position_tbdf = position_df[["patch", "max_position", "tourney_name", "date", "battle_conditions"]].style.apply(
        lambda row: [
            None,
            # f"color: {position_df[position_df.patch == row.patch].max_position_color.iloc[0]}",
            None,
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


def handle_not_graph_position_instead(average_foreground, colors, fig, rolling_average, stratas, tbdf):
    # tops = position_stratas[:-1][::-1]
    # strata_to_color = dict(zip(tops, position_colors[2:][::-1] + ["#FFFFFF"]))

    # best_position = tbdf.position.min()
    # worst_position = tbdf.position.max()

    # for strata in tops:
    #     if strata <= best_position:
    #         begin = strata
    #         break
    # else:
    #     begin = tops[0]

    # for strata in tops:
    #     if strata >= worst_position:
    #         end = strata
    #         break
    # else:
    #     end = tops[-1]

    # stratas_for_plot = [strata for strata in tops if strata >= begin and strata <= end]

    # champ_df = df[df.league == champ]  # backgrounds on graphs won't make sense for other leagues anyway
    # all_results = champ_df[champ_df.date.isin(tbdf.date.unique())]
    # all_results = all_results[all_results.position != -1]

    # min_by_strata = defaultdict(list)
    # max_by_strata = defaultdict(list)

    # for date, sdf in all_results.groupby("date"):
    #     for strata in tops:
    #         min_by_strata[strata].append(sdf[sdf.position <= strata].wave.min())
    #         max_by_strata[strata].append(sdf[sdf.position <= strata].wave.max())

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

    # fig.add_trace(
    #     go.Scatter(
    #         x=tbdf.date[::-1],
    #         y=max_by_strata[stratas_for_plot[0]],
    #         name=f"Max top {stratas_for_plot[0]}",
    #         line_dash="dot",
    #         marker=dict(size=0, opacity=0),
    #         opacity=0.6,
    #         line_color=html_to_rgb(strata_to_color[stratas_for_plot[0]], transparency=0.2),
    #     )
    # )

    # for strata in stratas_for_plot[1:]:
    #     fig.add_trace(
    #         go.Scatter(
    #             x=tbdf.date[::-1],
    #             y=min_by_strata[strata],
    #             name=f"Min top {strata}",
    #             line_dash="dot",
    #             marker=dict(size=0, opacity=0),
    #             opacity=0.6,
    #             fill="tonexty",
    #             line_color=html_to_rgb(strata_to_color[strata], transparency=0.2),
    #             fillcolor=html_to_rgb(strata_to_color[strata], transparency=0.1),
    #         )
    #     )

    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # min_ = min(tbdf.wave)
    # max_ = max(tbdf.wave)
    # for color_, strata in zip(colors, stratas):
    #     if max_ > strata > min_:
    #         fig.add_hline(y=strata, line_color=color_, line_dash="dash", opacity=0.4, line_width=3)


def handle_colors_dependant_on_patch(patch, player_df):
    if isinstance(patch, Patch):
        patch_df = player_df[player_df.patch == patch]

        if patch.version_minor >= 18:
            colors, stratas = colors_018, stratas_boundaries_018
        else:
            colors, stratas = colors_017, stratas_boundaries
    elif patch == Graph.last_16.value:
        patch_df = player_df[player_df.date.isin(sorted(player_df.date.unique())[-16:])]
        colors, stratas = colors_018, stratas_boundaries_018
    else:
        patch_df = player_df
        colors, stratas = colors_018, stratas_boundaries_018
    return colors, patch_df, stratas


def handle_sus_or_banned_ids(info_tab, id_, sus_ids):
    if id_ in get_banned_ids() or id_ in get_soft_banned_ids():
        info_tab.warning("This player is under review by the Support team.")
    elif id_ in sus_ids:
        info_tab.error("This player is under review by the Support team.")


def _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user):
    if user in (set(first_choices) | all_real_names | all_tourney_names):
        player_df = df[(df.real_name == user) | (df.tourney_name == user)]
    elif user in all_user_ids:
        player_df = df[df.id == id_mapping.get(user, user)]
    else:
        player_df = None

    return player_df


def find_player_across_leagues(user):
    for league in leagues:
        df = load_tourney_results(folder=league_to_folder[league])

        first_choices, all_real_names, all_tourney_names, all_user_ids, _ = get_player_list(df)

        if (player_df := _find_user(df, all_real_names, all_tourney_names, all_user_ids, first_choices, user)) is not None:
            df["league"] = league
            return df, player_df, league


if __name__ == "__main__":
    st.set_page_config(layout="centered")
    compute_player_lookup()


# import cProfile
# import pstats

# os.environ["HIDDEN_FEATURES"] = "false"

# pr = cProfile.Profile()
# pr.run("""compute_player_lookup(None, options=get_options(links=False), all_leagues=True)""")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
