import datetime
from collections import Counter, defaultdict
from functools import lru_cache, partial
from statistics import mean, median, stdev
from typing import List, Optional
from urllib.parse import urlencode

import extra_streamlit_components as stx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from components.constants import (
    colors_018,
    hardcoded_nicknames,
    position_colors,
    position_stratas,
    rehabilitated,
    rev_hardcoded_nicknames,
    strata_to_color_018,
    stratas_boundaries_018,
    sus_data,
    sus_ids,
    sus_person,
)
from components.data import load_data
from components.formatting import am_i_sus, color, color_nickname, color_nickname__top, color_position, color_position__top, color_top, strike

st.set_page_config(
    page_title="The Tower top200 tourney results",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "mailto:admin@thetower.lol",
    },
)

st.write(
    """<style>
.stRadio div {
    display: inline;
}
.stRadio > div > label {
    border-bottom: 1px solid #26282e;
    display: inline-block;
    padding: 4px 8px 4px 0px;
    margin: 0px;
    border-radius: 4px 4px 0 0;
    position: relative;
    top: 1px;
    # border-left: 5px solid #F63366;
}
.stRadio > div > label :hover {
    color: #F63366;
}
.stRadio input:checked + div {
    color: #F63366;
    border-left: 5px solid #F63366;
}
</style>""",
    unsafe_allow_html=True,
)


# st.info("We will be switching to new version, currently deployed at http://thetower.lol:8502/, any day now, pinky promise.")
st.info(
    "We have switched to the new version. I'm keeping this one alive for now here: http://thetower.lol:8502/, but beware that links will point to the new one."
)


@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()


def make_url(username):
    return f"<a href='http://thetower.lol?player={username}'>{username}</a>"


with st.sidebar:
    congrats_cookie_value = get_manager().get("congrats")

    league = st.radio("Choose league (champ is the supported one)", ("Champ", "Plat"))
    st.write("Experimental tweaks (use at your own peril)")
    links = st.checkbox("Links to users? (will make dataframe ugly)", value=get_manager().get("links"))
    congrats_toggle = st.checkbox("Do you like seeing congratulations?", value=congrats_cookie_value if congrats_cookie_value is not None else True)

    get_manager().set("links", links, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="links")
    get_manager().set("congrats", bool(congrats_toggle), expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="congrats")

if league == "Champ":
    folder = "data"
else:
    folder = "plat"

total_results, results_by_id, position_by_id = load_data(folder)
pretty_results = [pd.DataFrame(results) for name, results in total_results.items()]
new_patch = datetime.datetime.fromisoformat("2022-11-02").date()


pd.set_option("display.max_rows", None)


@lru_cache(maxsize=None)
def get_data_by_nickname(nickname):
    ids = []

    for id_, results in results_by_id.items():
        names = {name for _, name, _ in results}

        if nickname in names:
            ids.append((id_, results))

    return ids


@lru_cache(maxsize=None)
def get_majority_name(nickname):
    data = get_data_by_nickname(nickname)
    longest_datum = sorted(data, key=lambda datum: len(datum))[0][1]
    counter = Counter([nickname for _, nickname, _ in longest_datum])
    most_common_datas = counter.most_common()
    nickname_candidates = [datum[0] for datum in most_common_datas if datum[0]]
    return nickname_candidates[0] if nickname_candidates else ""


@lru_cache(maxsize=None)
def get_majority_name_by_id(id_):
    data = results_by_id[id_]
    counter = Counter([nickname for _, nickname, _ in data])
    return counter.most_common()[0][0]


@lru_cache(maxsize=None)
def get_real_nickname(id_, nickname=None):
    name = hardcoded_nicknames.get(id_)

    if name is None:
        if nickname is None:
            name = get_majority_name_by_id(id_)
        else:
            name = get_majority_name(nickname)

    return name


def translate_results(results):
    def translate_single(result, results):
        nickname = get_real_nickname(result[0])
        return result[0], result[1], nickname if nickname != result[1] else "", result[2]

    return [translate_single(result, results) for result in results]


@st.cache
def compute_roles():
    roles_by_id = {}

    for id_, results in results_by_id.items():
        try:
            max_result = max(filter(lambda row: row[0] >= new_patch, results), key=lambda row: row[2])
            max_wave = max_result[2]
        except ValueError:
            max_wave = 0

        if max_wave < stratas_boundaries_018[0]:
            role = 0
        else:
            strata = [strata_low for strata_low, strata_high in zip(stratas_boundaries_018, stratas_boundaries_018[1:]) if strata_low <= max_wave < strata_high]
            role = strata[0]

        roles_by_id[id_] = role

    return roles_by_id


roles_by_id = compute_roles()
colors_by_id = {id_: strata_to_color_018.get(strata, "grey") for id_, strata in roles_by_id.items()}


###############
### tab layout setup
###############

query = st.experimental_get_query_params()

if query:
    print(datetime.datetime.now(), query)

current_player: Optional[str]
compare_players: Optional[List[str]]

player = query.get("player")
compare_players = st.experimental_get_query_params().get("compare")

if player:
    current_player = player[0]
    functionality = "Player lookup"
elif compare_players:
    current_player = None
    functionality = "Comparison"
else:
    current_player = None
    functionality = None

tabs = ["Tourney results", "Player lookup", "Winners", "Comparison", "Top scores", "Breakdown", "About"]
functionality: str = st.radio("Which functionality to show?", tabs, index=0 if not functionality else tabs.index(functionality))


@lru_cache(maxsize=None)
def get_detail_data(user):
    if user_id := rev_hardcoded_nicknames.get(user):
        user_data = results_by_id[user_id]
        real_username = user
    elif user in results_by_id:
        user_id = user
        user_data = results_by_id[user]
        real_username = get_real_nickname(user)
    else:
        user_id, user_data = sorted(get_data_by_nickname(user), key=lambda datum: len(datum[1]))[-1]
        real_username = get_real_nickname(user_id)

    data = pd.DataFrame(user_data[::-1], columns=["date", "id", "wave"])
    data = data.drop_duplicates("date")

    position_data = pd.DataFrame(position_by_id[user_id], columns=["date", "nickname", "position"])[["date", "position"]]
    position_data = position_data.drop_duplicates("date")

    data = data.join(position_data.set_index("date"), on="date", how="inner")

    return real_username, user_id, data


###############
### tourney results
###############


def compute_tourney_results():
    # tab = tourney_results_tab
    tab = st

    def is_pb(id_, wave, date=None):
        try:
            rows = [row[2] for row in results_by_id[id_] if ((row[0] > new_patch) and (row[0] <= date if date else True))]
            return wave == max(rows)
        except ValueError:
            return False

    def two_best_scores(id_, date):
        sorted_results = sorted(
            filter(
                lambda row: row[0] > new_patch and row[0] <= date,
                results_by_id[id_],
            ),
            key=lambda row: row[2],
            reverse=True,
        )
        return sorted_results[:2]

    tourneys = sorted(total_results.keys(), reverse=True)
    tourney_file_name = tab.selectbox("Select tournament:", tourneys)

    previous_tourney = tourneys[index if (index := tourneys.index(tourney_file_name) + 1) < len(tourneys) else tourneys.index(tourney_file_name)]

    last_results = pd.DataFrame(translate_results(total_results[tourney_file_name]))
    previous_results = pd.DataFrame(translate_results(total_results[previous_tourney]))

    columns = ["id", "tourney name", "real name", "wave"]
    previous_results.columns = columns
    last_results.columns = columns

    last_results["pos"] = [previous_res[0] if len(previous_res := previous_results[previous_results["id"] == id_].index) else 200 for id_ in last_results["id"]]
    last_results["pos"] = last_results["pos"] - last_results.index
    last_results["pos"] = last_results.apply(lambda row: ("+" if row["pos"] >= 0 else "") + str(row["pos"]), axis=1)
    last_results["pos"] = last_results.apply(lambda row: row["pos"] if row["pos"] != "+0" else "==", axis=1)
    last_results["diff"] = [
        previous_res[0] if (previous_res := list(previous_results[previous_results["id"] == id_].wave)) else 0 for id_ in last_results["id"]
    ]
    last_results["diff"][last_results["diff"] != 0] = last_results["wave"][last_results["diff"] != 0] - last_results["diff"][last_results["diff"] != 0]
    # last_results["diff"] = last_results.apply(lambda row: ("+" if row["diff"] >= 0 else "") + str(row["diff"]), axis=1)
    # last_results["diff"] = last_results.apply(lambda row: row["diff"] if row["diff"] != "+0" else "==", axis=1)
    # last_results["diff"] = last_results.apply(lambda row: row["diff"] + (" (pb!)" if is_pb(row["id"], row["wave"]) else ""), axis=1)

    # add medals
    place_counter = 1
    real_counter = 1

    for index, result in enumerate(last_results.loc):
        if result["id"] not in sus_ids:
            if result["real name"] == "":
                last_results.loc[index, "real name"] = result["tourney name"]

            if place_counter == 1:
                last_results.loc[index, "real name"] += " 🥇"
            if place_counter == 2:
                last_results.loc[index, "real name"] += " 🥈"
            if place_counter == 3:
                last_results.loc[index, "real name"] += " 🥉"

            place_counter += 1
        real_counter += 1

        if real_counter > 200:
            break

    res_col, congrats_col = tab.columns([1, 1])

    if congrats_toggle:
        with tab.expander("Congrats! 🎉"):
            for strata_name, (strata_bottom, strata_top) in [
                ("toxic green names", [3000, 4000]),
                ("saudade green names", [2500, 3000]),
                ("rednames", [2000, 2500]),
                ("darkgreen names", [1750, 2000]),
                ("blue names", [1500, 1750]),
            ]:
                rednames = last_results[last_results["wave"] < strata_top]
                rednames = rednames[rednames["wave"] >= strata_bottom]
                new_rednames = []

                for _, redname_row in rednames.iterrows():
                    redname = redname_row["tourney name"]

                    if redname_row.id in sus_ids:
                        continue

                    redname_real_username, redname_user_id, redname_data = get_detail_data(redname)

                    redname_data = redname_data[redname_data["date"] > new_patch]

                    redname_particular_data = redname_data[redname_data["date"] <= tourney_file_name]
                    redname_particular_data = redname_particular_data[redname_particular_data["wave"] >= strata_bottom]

                    if len(redname_particular_data) == 1:
                        new_rednames.append(redname_real_username)

                if new_rednames:
                    colored_names = [f"<font color='{strata_to_color_018[strata_bottom]}'>{name}</font>" for name in new_rednames if name]
                    st.write(f"Congratulations for new {strata_name} {', '.join(colored_names)}!", unsafe_allow_html=True)

            pbs = []

            for _, row in last_results.iterrows():
                if is_pb(row["id"], row["wave"], date=tourney_file_name) and row["id"] not in sus_ids and row["tourney name"]:
                    two_best = two_best_scores(row["id"], date=tourney_file_name)

                    if len(two_best) == 2 and two_best[0][2] > two_best[1][2]:
                        pb_by = two_best[0][2] - two_best[1][2]
                        how_long = two_best[0][0] - two_best[1][0]
                        role = colors_by_id[row["id"]]

                        if how_long.days > 30:
                            backhand = "It took so long!"
                        elif row["id"] == "830D4F2F4E322579":
                            backhand = "haxxor!!111"
                        elif row["id"] == "BCCBAF556C357D63":
                            backhand = "Forever red in our hearts!"
                        elif pb_by > 300:
                            backhand = "How did you get such a big jump??"
                        elif how_long.days in [3, 4]:
                            backhand = "Woah! So soon?"
                        elif row["id"] == "BB8938ABCD564BD3":
                            backhand = "It's ok, don't worry Pasco! Red nickname next time."
                        else:
                            backhand = ""

                        pbs.append(
                            f"<font color='{role}'>{row['real name']}</font>, PB of <b>{two_best[0][2]}</b> by <b>{pb_by}</b> waves, for which they waited <b>{how_long.days}</b> days. {backhand}"
                        )

            st.write(f"New PBs!")

            for pb in pbs:
                st.write(pb, unsafe_allow_html=True)

    # sus
    last_results["real name"] = last_results.apply(lambda row: sus_person if row["id"] in sus_ids else row["real name"], axis=1)
    last_results["tourney name"] = last_results.apply(lambda row: strike(row["tourney name"]) if row["id"] in sus_ids else row["tourney name"], axis=1)
    last_results["index"] = list(range(1, len(last_results) + 1))
    last_results = last_results.set_index(keys="index")

    to_be_displayed = (
        last_results[["pos", "tourney name", "real name", "wave", "diff", "id"]]
        .style.applymap(color, subset=["diff", "pos"])
        .applymap(color_top, subset=["wave"])
        .apply(partial(color_nickname, roles_by_id=roles_by_id), axis=1)
        .applymap(am_i_sus, subset=["real name"])
        .bar(subset=["diff"], cmap="RdYlGn")
        .hide(subset=["id"], axis=1, names=True)
    )

    if links:
        to_be_displayed = to_be_displayed.format(make_url, subset=["real name"]).to_html(escape=False)
        tab.write(to_be_displayed, unsafe_allow_html=True)
    else:
        tab.dataframe(to_be_displayed, use_container_width=True, height=800)


###############
### winners
###############


def compute_winners():
    # tab = winners_tab
    tab = st

    pies_tab, roll_your_pie_tab, averages_tab, additional_analysis_tab = tab.tabs(["Pies", "Bake your own pie", "Averages", "Additional analysis"])

    def get_winner(results, top_k=1):
        winners = []

        for result in results:
            if result[0] not in sus_ids:
                winners.append(get_real_nickname(result[0]))

                if len(winners) == top_k:
                    return winners

    winner_score = {
        0: 5,
        1: 3,
        2: 2,
    }

    previous_tournaments = sorted(total_results.items(), reverse=True)
    last_n_tournaments = pies_tab.slider("How many past tournaments?", min_value=1, max_value=len(previous_tournaments), value=len(previous_tournaments))

    winners_data = [get_winner(results[1])[0] for results in previous_tournaments[:last_n_tournaments]]
    winners_df = pd.DataFrame(tuple(Counter(winners_data).items()))
    winners_df.columns = ["name", "count"]

    fig = px.pie(winners_df, values="count", names="name", title="Winners of champ, courtesy of Jim")
    fig.update_traces(textinfo="value")
    pies_tab.plotly_chart(fig)

    winners_score_data = [
        {key: winner_score[index] for index, key in enumerate(get_winner(results[1], top_k=3))} for results in previous_tournaments[:last_n_tournaments]
    ]

    winners_score = defaultdict(int)

    for scores in winners_score_data:
        for username, score in scores.items():
            winners_score[username] += score

    winners_score_df = pd.DataFrame(sorted(winners_score.items(), key=lambda x: x[1], reverse=True))
    winners_score_df.columns = ["name", "score"]
    fig = px.pie(winners_score_df, values="score", names="name", title="Winners by score: 1st gets 5 points, 2nd gets 3 points, and 3rd gets 2.")
    fig.update_traces(textinfo="value")
    pies_tab.plotly_chart(fig)

    skye_score = {
        0: 10,
        1: 5,
        2: 3,
        3: 2,
        4: 2,
        5: 1,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
    }
    winners_score_data_2 = [
        {key: skye_score[index] for index, key in enumerate(get_winner(results[1], top_k=10))} for results in previous_tournaments[:last_n_tournaments]
    ]

    winners_score_2 = defaultdict(int)

    for scores in winners_score_data_2:
        for username, score in scores.items():
            winners_score_2[username] += score

    winners_score_df_2 = pd.DataFrame(sorted(winners_score_2.items(), key=lambda x: x[1], reverse=True))
    winners_score_df_2.columns = ["name", "score"]
    fig = px.pie(winners_score_df_2, values="score", names="name", title="Skye's scoring: 10 for first, 5 for second, 3 for third, 2 for top 5, 1 for top 10")
    fig.update_traces(textinfo="value")
    pies_tab.plotly_chart(fig)

    places = range(1, 11)

    roll_columns = roll_your_pie_tab.columns([1, 1, 1, 1, 1])

    sliders = {
        place - 1: roll_columns[(place - 1) % 5].slider(f"How many points for place {place}?", min_value=0, max_value=10, value=winner_score.get(place - 1, 0))
        for place in places
    }

    winners_score_data_sliders = [
        {key: sliders[index] for index, key in enumerate(get_winner(results[1], top_k=10))} for results in previous_tournaments[:last_n_tournaments]
    ]

    winners_score_roll = defaultdict(int)

    for scores in winners_score_data_sliders:
        for username, score in scores.items():
            winners_score_roll[username] += score

    colormap = roll_your_pie_tab.selectbox(
        "Color map?", [item for item in dir(px.colors.sequential) if not item.startswith("__") and not item.startswith("swatches")]
    )

    winners_score_df_roll = pd.DataFrame(sorted(winners_score_roll.items(), key=lambda x: x[1], reverse=True))
    winners_score_df_roll.columns = ["name", "score"]
    fig = px.pie(
        winners_score_df_roll, values="score", names="name", title="Bake your own pie", color_discrete_sequence=getattr(px.colors.sequential, colormap)
    )
    fig.update_traces(textinfo="value")
    roll_your_pie_tab.plotly_chart(fig)

    last_n_tournaments = averages_tab.slider("How many past tournaments?", min_value=1, max_value=len(previous_tournaments), value=20)
    top_n = averages_tab.slider("How many players to plot?", min_value=1, max_value=200, value=50)

    def get_stats_data(last_n_tournaments, top_n, start_tournament=0):
        tourneys = sorted(total_results.keys(), reverse=True)

        current_top = [row[0] for row in total_results[tourneys[0]] if row[0] not in sus_ids]
        ids_in_last_n = [{res[0] for res in total_results[tourney_date]} for tourney_date in tourneys[start_tournament:last_n_tournaments]]
        consistent_top_ids = [id_ for id_ in current_top if all({id_ in result_ids for result_ids in ids_in_last_n})][:top_n]

        means = [mean([result[2] for result in results_by_id[id_][::-1][start_tournament:last_n_tournaments]]) for id_ in consistent_top_ids]
        stdevs = [
            stdev(data) if len(data := [result[2] for result in results_by_id[id_][::-1][start_tournament:last_n_tournaments]]) > 1 else 0
            for id_ in consistent_top_ids
        ]

        median_mean = median(means)
        median_stdev = median(stdevs)

        return consistent_top_ids, means, stdevs, median_mean, median_stdev

    consistent_top_ids, means, stdevs, median_mean, median_stdev = get_stats_data(last_n_tournaments, top_n)
    current_top_nicknames = [get_real_nickname(id_) for id_ in consistent_top_ids]
    total_data = sorted(zip(current_top_nicknames, means, stdevs), key=lambda x: x[1], reverse=True)

    averages_tab.write(f"Median score in the group: {median_mean}, with median stdev {median_stdev}.")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Player",
            x=[datum[0] for datum in total_data],
            y=[datum[1] for datum in total_data],
            error_y=dict(type="data", array=[datum[2] for datum in total_data]),
        )
    )
    fig.update_layout(barmode="stack", title=f"Average performance of the last tourney's top{top_n} in last {last_n_tournaments} tournaments")

    for color_, strata in zip(colors_018[:-1], stratas_boundaries_018[:-1]):
        fig.add_hline(
            y=strata,
            line_color=color_,
            line_dash="dash",
            opacity=0.4,
        )
    for color_, strata in zip(position_colors, position_stratas):
        if strata <= top_n:
            fig.add_vline(x=strata - 0.5, line_width=2, line_dash="dash", line_color=color_)

    averages_tab.plotly_chart(fig)

    df_data = [get_stats_data(tourney_number, top_n, start_tournament=tourney_number - 4)[-2:] for tourney_number in range(5, last_n_tournaments)]
    df_data = [[int(round(mean_, 0)), int(round(stdev_, 0))] for mean_, stdev_ in df_data]
    df = pd.DataFrame(df_data)
    df.columns = ["median mean wave", "median stdev of waves"]
    df["4 tournaments starting n tourneys ago (moving window)"] = list(range(5, len(df) + 5))
    additional_analysis_tab.dataframe(df)

    figure = px.scatter(df, x="4 tournaments starting n tourneys ago (moving window)", y="median mean wave")
    additional_analysis_tab.plotly_chart(figure)
    figure = px.scatter(df, x="4 tournaments starting n tourneys ago (moving window)", y="median stdev of waves")
    additional_analysis_tab.plotly_chart(figure)


###############
### player lookup
###############


@lru_cache()
def get_player_list():
    last_top_scorers = [(row[0], row[1]) for row in list(total_results.values())[-1]]

    for scorer_id, scorer in last_top_scorers:
        if scorer_id not in sus_ids:
            last_top_scorer = scorer
            break

    return (
        [current_player if current_player else last_top_scorer]
        + sorted({result for tourney_file in total_results.values() for _, result, _ in tourney_file} | set(hardcoded_nicknames.values()))
        + sorted(results_by_id.keys())
    )


def compute_player_lookup():
    # tab = player_lookup_tab
    tab = st

    user = tab.selectbox("Which user would you like to lookup?", get_player_list())
    tab.code("http://thetower.lol?" + urlencode({"player": user}, doseq=True))

    data_assuming_nickname = get_data_by_nickname(user)

    if len(data_assuming_nickname) > 2:
        datas = sorted(data_assuming_nickname, key=lambda x: len(x[1]), reverse=True)
        user = st.selectbox("Since multiple players have the same username, please choose id", [datum[0] for datum in datas])

    real_username, user_id, data = get_detail_data(user)

    max_wave_data = data[data["wave"] == data["wave"].max()]

    data_new = data[data["date"] > new_patch]

    max_wave_data_new = data_new[data_new["wave"] == data_new["wave"].max()]
    mean_wave = data_new["wave"].mean()
    std_wave = data_new["wave"].std()

    last_5_data = data.loc[:4]
    mean_wave_last = last_5_data["wave"].mean()
    std_wave_last = last_5_data["wave"].std()

    def extract_one(series_one_or_two):
        if len(series_one_or_two) > 1:
            wave = list(series_one_or_two.wave)[0]
        else:
            wave = int(series_one_or_two.wave)
        id_ = list(series_one_or_two.id)[0]
        date = list(series_one_or_two.date)[0]
        return wave, id_, date

    role = strata_to_color_018.get(roles_by_id[user_id], "#AAAAAA")

    if not max_wave_data_new.empty:
        max_wave, max_id, max_date = extract_one(max_wave_data_new)
        tab.write(
            f"Max wave for <font color='{role}'>{real_username}</font> in champ _since 0.16_: **{max_wave}**, as {max_id} on {max_date}", unsafe_allow_html=True
        )
        tab.write(
            f"Average wave for <font color='{role}'>{real_username}</font> in champ _since 0.16_: **{round(mean_wave, 2)}** with the standard deviation of {round(std_wave, 2)}",
            unsafe_allow_html=True,
        )

    if not last_5_data.empty:
        tab.write(
            f"Average wave for <font color='{role}'>{real_username}</font> in champ for the last 5 tournaments: **{round(mean_wave_last, 2)}** with the standard deviation of {round(std_wave_last, 2)}",
            unsafe_allow_html=True,
        )

    max_wave, max_id, max_date = extract_one(max_wave_data)

    tab.write(f"Max wave for <font color='{role}'>{real_username}</font> in champ: **{max_wave}**, as {max_id} on {max_date}", unsafe_allow_html=True)
    tab.write(f"User Id used: {user_id}")

    is_data_full_box, graph_position_instead_box = tab.columns(2)
    is_data_full = is_data_full_box.checkbox("Graph all data? (not just 0.16)")
    graph_position_instead = graph_position_instead_box.checkbox("Graph position instead")

    data_to_use = data if is_data_full else data_new

    if graph_position_instead:
        position_data = pd.DataFrame(position_by_id[user_id], columns=["date", "nickname", "position"])
        position_data_new = position_data[position_data["date"] > new_patch]
        position_data_to_use = position_data if is_data_full else position_data_new

    if len(data_to_use) > 1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not graph_position_instead:
            fig.add_trace(
                go.Scatter(x=data_to_use.date, y=data_to_use.wave, name="Wave (left axis)"),
                secondary_y=False,
            )
        else:
            fig.add_trace(
                go.Scatter(x=position_data_to_use.date, y=position_data_to_use.position, name="Tourney position"),
                secondary_y=True,
            )

        fig.update_yaxes(secondary_y=True, range=[200, 0])

        min_ = min(data_new.wave)
        max_ = max(data_new.wave)

        for color_, strata in zip(colors_018, stratas_boundaries_018):
            if max_ > strata > min_:
                fig.add_hline(
                    y=strata,
                    line_color=color_,
                    line_dash="dash",
                    opacity=0.4,
                )
        tab.plotly_chart(fig)

    to_be_displayed = data.style.applymap(color_top, subset=["wave"]).applymap(color_position, subset=["position"])
    tab.dataframe(to_be_displayed, use_container_width=True, height=600)

    with tab.expander("Debug log..."):
        st.write(get_data_by_nickname(user))


###############
### top scores
###############


@lru_cache()
def get_top_scores_df():
    total_scores = []

    for tourney_date, tourney_results in total_results.items():
        if league == "Champ" and tourney_date <= new_patch:
            continue

        for score in tourney_results:
            id_ = score[0]
            wave = score[2]
            position = [pos_data for pos_data in position_by_id[id_] if pos_data[0] == tourney_date][0][2]
            total_scores.append([tourney_date, get_real_nickname(id_), wave, position, id_])

    top_scores = [score for score in sorted(total_scores, key=lambda x: x[2], reverse=True) if score[4] not in sus_ids]

    df = pd.DataFrame(top_scores, columns=["date", "regular nickname", "wave", "position", "id"])

    overall_df = df.loc[:1000]
    overall_df["index"] = list(range(1, len(overall_df) + 1))
    overall_df = overall_df.set_index(keys="index")

    peeps = set()
    condensed_scores = []

    for top_score in top_scores:
        if top_score[1] in peeps:
            continue

        condensed_scores.append(top_score)
        peeps.add(top_score[1])

    condensed_df = pd.DataFrame(condensed_scores, columns=["date", "regular nickname", "wave", "position", "id"])
    condensed_df = condensed_df.loc[:200]
    condensed_df["index"] = list(range(1, len(condensed_df) + 1))
    condensed_df = condensed_df.set_index(keys="index")

    return overall_df, condensed_df


def compute_top_scores():
    # tab = top_scores_tab
    tab = st

    tab.title("Top tournament scores")
    tab.write(
        "This tab only collects data from 0.16 onwards. I tried to manually remove some sus scores, please let me know on discord if there's anything left."
        if league == "Champ"
        else "This data can be shit, as there were a lot of hackers in plat"
    )

    tab.write("Counting only highest per person:")

    overall_df, condensed_df = get_top_scores_df()

    condensed_tbd = (
        condensed_df.style.applymap(color_top, subset=["wave"])
        .apply(partial(color_nickname__top, roles_by_id=roles_by_id), axis=1)
        .applymap(color_position__top, subset=["position"])
    )

    if links:
        condensed_tbd = condensed_tbd.format(make_url, subset=["regular nickname"]).to_html(escape=False)
        tab.write(condensed_tbd, unsafe_allow_html=True)
    else:
        tab.dataframe(condensed_tbd, use_container_width=True, height=400)

    overall_tbd = (
        overall_df.style.applymap(color_top, subset=["wave"])
        .apply(partial(color_nickname__top, roles_by_id=roles_by_id), axis=1)
        .applymap(color_position__top, subset=["position"])
    )

    tab.write("Overall:")

    if links:
        overall_tbd = overall_tbd.format(make_url, subset=["regular nickname"]).to_html(escape=False)
        tab.write(overall_tbd, unsafe_allow_html=True)
    else:
        tab.dataframe(overall_tbd, use_container_width=True, height=400)


###############
### breakdown
###############


def compute_breakdown():
    # tab = breakdown_tab
    tab = st

    def get_stratified_counts(results):
        return {
            lower_strata: sum(higher_strata >= result[2] > lower_strata for result in results)
            for lower_strata, higher_strata in zip(stratas_boundaries_018, stratas_boundaries_018[1:])
        }

    def get_up_or_down(previous_results, next_results, date):
        previous_lookup = {id_: wave for id_, _, wave in previous_results}
        next_lookup = {id_: wave for id_, _, wave in next_results}

        breakdown_data = []

        for id_, next_wave in next_lookup.items():
            previous_wave = previous_lookup.get(id_)

            if previous_wave is None:
                continue

            if previous_wave < next_wave:
                value = "up"
            elif previous_wave > next_wave:
                value = "down"
            else:
                value = "same"

            breakdown_data.append(value)

        return Counter(breakdown_data)

    stratified_results = {date: get_stratified_counts(results) for date, results in total_results.items()}
    total_sorted = sorted(total_results.items())
    up_or_down_results = {
        date: get_up_or_down(previous_results, new_results, date) for (_, previous_results), (date, new_results) in zip(total_sorted, total_sorted[1:])
    }
    restratified_results = {
        strata: [stratified_result.get(strata, 0) for date, stratified_result in stratified_results.items()] for strata in stratas_boundaries_018
    }
    restratified_up_or_down = {strata: [up_or_down.get(strata, 0) for date, up_or_down in up_or_down_results.items()] for strata in ["up", "same", "down"]}
    restratified_up_or_down = {
        **restratified_up_or_down,
        "not on the list": [
            200 - (i + j + k) for i, j, k in zip(restratified_up_or_down["down"], restratified_up_or_down["same"], restratified_up_or_down["up"])
        ],
    }

    if 100000 in stratas_boundaries_018:
        stratas_boundaries_018.pop(-1)
    restratified_results.pop(10000, None)

    stratified_plot_data = [
        go.Bar(
            name=name,
            x=list(stratified_results.keys()),
            y=results,
        )
        for name, results in restratified_results.items()
    ]

    for datum, color_ in zip(stratified_plot_data, colors_018):
        datum.update(marker_color=color_)

    fig = go.Figure(data=stratified_plot_data)
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode="stack", title="Role counts per tournament, courtesy of ObsUK")

    tab.plotly_chart(fig)

    up_or_down_plot_data = [
        go.Bar(
            name=name,
            x=list(up_or_down_results.keys()),
            y=results,
        )
        for name, results in restratified_up_or_down.items()
    ]

    fig = go.Figure(data=up_or_down_plot_data)
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode="stack", title="How many players went up or down in waves?")

    tab.plotly_chart(fig)


###############
### comparison
###############


def compute_comparison():
    # tab = comparison_tab
    tab = st

    tab.title("See rating progression of multiple players")

    top5 = tab.checkbox("Compare 0.16 top5 players?")

    _, condensed_df = get_top_scores_df()

    if top5:
        default_value = list(condensed_df.loc[:5]["regular nickname"])
    elif compare_players:
        default_value = list(compare_players)
    else:
        default_value = []

    users = tab.multiselect("Which players to compare?", get_player_list(), default=default_value)

    if users:
        datas = []
        position_datas = []
        for user in users:
            real_username, user_id, data = get_detail_data(user)
            data["user"] = [real_username] * len(data)
            data = data[data["date"] > new_patch]
            position_data = pd.DataFrame(position_by_id[user_id], columns=["date", "nickname", "position"])
            position_data["user"] = [real_username] * len(position_data)
            position_data = position_data[position_data["date"] > new_patch]
            position_data = position_data.reset_index()
            position_data["wave"] = data.wave

            if len(data) >= 2:
                datas.append(data)
                position_datas.append(position_data)

        datas = sorted(datas, key=lambda datum: max(datum.wave), reverse=True)
        position_datas = sorted(position_datas, key=lambda datum: max(datum.wave), reverse=True)

        if datas:
            summary = pd.DataFrame(
                [
                    [
                        data.user.unique()[0],
                        len(data),
                        max(data.wave),
                        int(round(median(data.wave), 0)),
                        int(round(stdev(data.wave), 0)),
                        min(data.wave),
                    ]
                    for data in datas
                ],
                columns=["User", "No. times in champ 0.16", "PB", "Median", "Stdev", "Lowest score on record"],
            )
            summary.set_index(keys="User")

            if links:
                to_be_displayed = summary.style.format(make_url, subset=["User"]).to_html(escape=False)
                tab.write(to_be_displayed, unsafe_allow_html=True)
            else:
                tab.dataframe(summary, use_container_width=True)

            tab.code("http://thetower.lol?" + urlencode({"compare": users}, doseq=True))

            pd_datas = pd.concat(datas)
            fig = px.line(pd_datas, x="date", y="wave", color="user", markers=True)

            min_ = min(pd_datas.wave)
            max_ = max(pd_datas.wave)

            for color_, strata in zip(colors_018, stratas_boundaries_018):
                if max_ > strata > min_:
                    fig.add_hline(
                        y=strata,
                        line_color=color_,
                        line_dash="dash",
                        opacity=0.4,
                    )
            tab.plotly_chart(fig)

            results_together = pd.concat(position_datas)
            fig = px.line(results_together, x="date", y="position", color="user", markers=True)
            fig.update_yaxes(range=[max(results_together.position), min(results_together.position)])
            tab.plotly_chart(fig)


###############
### sustab
###############


def compute_about():
    # tab = sus_tab
    tab = st

    tab.title("About")
    tab.markdown("My discord id is `098799#0707`.")
    tab.markdown("Thanks to `Milamber33` for a lot of help with css and other things.")
    tab.markdown("Thanks to `Jim808` and `ObsUK` for a graph ideas and encouragement.")

    tab.header("Sus people")
    tab.write(
        """Sometimes on the leaderboards there are suspicious individuals that had achieved hard to believe tournament scores. The system doesn't necessarily manage to detect and flag all of them, so some postprocessing is required. There's no official approval board for this, I'm just a guy on discord that tries to analyze results. If you'd like your name rehabilitated, please join the tower discord and talk to us in the tournament channel."""
    )
    tab.write(
        """It is important to note that **not all people listed here are confirmed hackers**!! In fact, Pog has explicitly stated that some of them may not be hackers, or at least it cannot be proven at this point."""
    )

    tab.write("Currently, sus people are:")
    tab.write(pd.DataFrame(sorted([(nickname, id_) for nickname, id_ in sus_data]), columns=["nickname", "id"]))

    tab.header("Vindicated")
    tab.write("Previously on the sus list but vindicated by the tower staff:")
    tab.write(sorted([nickname for nickname, id_ in rehabilitated]))


# if compute_order == "player":
#     compute_player_lookup()
#     compute_tourney_results()
#     compute_winners()
#     compute_top_scores()
#     compute_comparison()
#     compute_breakdown()
#     compute_sus()
# elif compute_order == "comparison":
#     compute_top_scores()
#     compute_player_lookup()
#     compute_comparison()
#     compute_tourney_results()
#     compute_winners()
#     compute_breakdown()
#     compute_sus()
# elif compute_order == "normal":
#     compute_tourney_results()
#     compute_winners()
#     compute_player_lookup()
#     compute_top_scores()
#     compute_comparison()
#     compute_breakdown(stratas)
#     compute_sus()


function = f"compute_{'_'.join(functionality.lower().split())}"
globals()[function]()
