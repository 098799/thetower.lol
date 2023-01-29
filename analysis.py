import datetime
from collections import Counter
from functools import lru_cache
from statistics import mean, stdev
from typing import List, Optional
from urllib.parse import urlencode

import extra_streamlit_components as stx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from formatting import am_i_sus, color, color_top, strike
from hardcoding import colors, hardcoded_nicknames, rev_hardcoded_nicknames, stratas, sus, sus_person
from load_data import load_data

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
}
.stRadio > div > label :hover {
    color: #F63366;
}
}
</style>""",
    unsafe_allow_html=True,
)


@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()


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
    return counter.most_common()[0][0]


@lru_cache(maxsize=None)
def get_real_nickname(id_, nickname):
    return hardcoded_nicknames.get(id_, get_majority_name(nickname))


def translate_results(results):
    def translate_single(result, results):
        nickname = get_real_nickname(result[0], result[1])
        return result[0], result[1], nickname if nickname != result[1] else "", result[2]

    return [translate_single(result, results) for result in results]


###############
### tab layout setup
###############

query = st.experimental_get_query_params()

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

tabs = ["Tourney results", "Player lookup", "Winners", "Comparison", "Top scores", "Breakdown", "sus"]
functionality: str = st.radio("Which functionality to show?", tabs, index=0 if not functionality else tabs.index(functionality))


@lru_cache(maxsize=None)
def get_detail_data(user):
    if user_id := rev_hardcoded_nicknames.get(user):
        user_data = results_by_id[user_id]
        real_username = user
    else:
        user_id, user_data = sorted(get_data_by_nickname(user), key=lambda datum: len(datum[1]))[-1]
        real_username = get_real_nickname(user_id, user)

    data = pd.DataFrame(user_data[::-1])
    data.columns = ["date", "id", "wave"]
    return real_username, user_id, data


###############
### tourney results
###############


def compute_tourney_results():
    # tab = tourney_results_tab
    tab = st

    def is_pb(id_, wave):
        try:
            return wave == max(row[2] for row in results_by_id[id_] if row[0] > new_patch)
        except ValueError:
            return False

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
    last_results["diff"] = last_results["wave"] - last_results["diff"]
    last_results["diff"] = last_results.apply(lambda row: ("+" if row["diff"] >= 0 else "") + str(row["diff"]), axis=1)
    last_results["diff"] = last_results.apply(lambda row: row["diff"] if row["diff"] != "+0" else "==", axis=1)
    last_results["diff"] = last_results.apply(lambda row: row["diff"] + (" (pb!)" if is_pb(row["id"], row["wave"]) else ""), axis=1)

    # add medals
    place_counter = 1

    for index, result in enumerate(last_results.loc(0)):
        if result["tourney name"] not in sus:
            if result["real name"] == "":
                last_results.loc[index, "real name"] = result["tourney name"]

            if place_counter == 1:
                last_results.loc[index, "real name"] += " 🥇"
            if place_counter == 2:
                last_results.loc[index, "real name"] += " 🥈"
            if place_counter == 3:
                last_results.loc[index, "real name"] += " 🥉"

            place_counter += 1

        if place_counter > 3:
            break

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

                    if redname in sus:
                        continue

                    redname_real_username, redname_user_id, redname_data = get_detail_data(redname)

                    redname_data = redname_data[redname_data["date"] > new_patch]

                    redname_particular_data = redname_data[redname_data["date"] <= tourney_file_name]
                    redname_particular_data = redname_particular_data[redname_particular_data["wave"] >= strata_bottom]

                    if len(redname_particular_data) == 1:
                        new_rednames.append(redname_real_username)

                if new_rednames:
                    st.write(f"Congratulations for new {strata_name} {', '.join(new_rednames)}!")

    # sus
    last_results["real name"] = last_results.apply(lambda row: sus_person if row["tourney name"] in sus else row["real name"], axis=1)
    last_results["tourney name"] = last_results.apply(lambda row: strike(row["tourney name"]) if row["tourney name"] in sus else row["tourney name"], axis=1)
    last_results["index"] = list(range(1, len(last_results) + 1))
    last_results = last_results.set_index(keys="index")

    def make_url(username):
        return f"<a href='http://thetower.lol?player={username}'>{username}</a>"

    to_be_displayed = (
        last_results[["pos", "tourney name", "real name", "wave", "diff"]]
        .style.applymap(color, subset=["diff", "pos"])
        .applymap(color_top, subset=["wave"])
        .applymap(am_i_sus, subset=["real name"])
    )

    if links:
        to_be_displayed = to_be_displayed.format(make_url, subset=["tourney name"]).to_html(escape=False)
        tab.write(to_be_displayed, unsafe_allow_html=True)
    else:
        tab.dataframe(to_be_displayed, use_container_width=True, height=800)


###############
### winners
###############


def compute_winners():
    # tab = winners_tab
    tab = st

    def get_winner(results):
        for result in results:
            nickname = get_real_nickname(result[0], result[1])
            if nickname not in sus:
                return nickname

    previous_tournaments = sorted(total_results.items(), reverse=True)
    last_n_tournaments = tab.slider("How many past tournaments?", min_value=1, max_value=len(previous_tournaments), value=len(previous_tournaments))

    winners_data = [get_winner(results[1]) for results in previous_tournaments[:last_n_tournaments]]
    winners_df = pd.DataFrame(tuple(Counter(winners_data).items()))
    winners_df.columns = ["name", "count"]
    fig = px.pie(winners_df, values="count", names="name", title="Winners of champ, courtesy of Jim")
    fig.update_traces(textinfo="value")
    tab.plotly_chart(fig)

    top_n = tab.slider("How many players to plot?", min_value=1, max_value=200, value=100)

    tourneys = sorted(total_results.keys(), reverse=True)
    current_top_nicknames = [get_real_nickname(row[0], row[1]) for row in total_results[tourneys[0]][:top_n] if row[1] not in sus]
    current_top = [row[0] for row in total_results[tourneys[0]][:top_n] if row[1] not in sus]
    means = [mean([result[2] for result in results_by_id[id_][-last_n_tournaments:]]) for id_ in current_top]
    stdevs = [stdev(data) if len(data := [result[2] for result in results_by_id[id_][-last_n_tournaments:]]) > 1 else 0 for id_ in current_top]

    total_data = sorted(zip(current_top_nicknames, means, stdevs), key=lambda x: x[1], reverse=True)

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

    for color_, strata in zip(colors[:-1], stratas[:-1]):
        fig.add_hline(
            y=strata,
            line_color=color_,
            line_dash="dash",
            opacity=0.4,
        )
    for color_, strata in zip(["blue", "green", "#664620", "red"], [10, 50, 100, 200]):
        if strata <= top_n:
            fig.add_vline(x=strata - 0.5, line_width=2, line_dash="dash", line_color=color_)

    tab.plotly_chart(fig)


###############
### player lookup
###############


@lru_cache()
def get_player_list():
    last_top_scorers = [row[1] for row in list(total_results.values())[-1]]

    for scorer in last_top_scorers:
        if scorer not in sus:
            last_top_scorer = scorer
            break

    return [current_player if current_player else last_top_scorer] + sorted(
        {result for tourney_file in total_results.values() for _, result, _ in tourney_file} | set(hardcoded_nicknames.values())
    )


def compute_player_lookup():
    # tab = player_lookup_tab
    tab = st

    selectbox_field, toggle_position = tab.columns([3, 1])

    user = selectbox_field.selectbox("Which user would you like to lookup?", get_player_list())
    graph_position_instead = toggle_position.checkbox("Graph position instead")

    real_username, user_id, data = get_detail_data(user)
    max_wave_data = data[data["wave"] == data["wave"].max()]

    data_new = data[data["date"] > new_patch]

    max_wave_data_new = data_new[data_new["wave"] == data_new["wave"].max()]
    mean_wave = data_new["wave"].mean()
    std_wave = data_new["wave"].std()

    last_5_data = data.loc(0)[:4]
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

    if not max_wave_data_new.empty:
        max_wave, max_id, max_date = extract_one(max_wave_data_new)
        tab.write(f"Max wave for {real_username} in champ _since 0.16_: **{max_wave}**, as {max_id} on {max_date}")
        tab.write(f"Average wave for {real_username} in champ _since 0.16_: **{round(mean_wave, 2)}** with the standard deviation of {round(std_wave, 2)}")

    if not last_5_data.empty:
        tab.write(
            f"Average wave for {real_username} in champ for the last 5 tournaments: **{round(mean_wave_last, 2)}** with the standard deviation of {round(std_wave_last, 2)}"
        )

    max_wave, max_id, max_date = extract_one(max_wave_data)

    tab.write(f"Max wave for {real_username} in champ: **{max_wave}**, as {max_id} on {max_date}")
    tab.write(f"User Id used: {user_id}")
    is_data_full = tab.checkbox("Graph all data? (not just 0.16)")

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

        fig.update_yaxes(secondary_y=True, range=[0, 200])

        min_ = min(data_new.wave)
        max_ = max(data_new.wave)

        for color_, strata in zip(colors, stratas):
            if max_ > strata > min_:
                fig.add_hline(
                    y=strata,
                    line_color=color_,
                    line_dash="dash",
                    opacity=0.4,
                )
        tab.plotly_chart(fig)

    tab.dataframe(data.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=600)

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
            total_scores.append([tourney_date, get_real_nickname(score[0], score[1]), score[2]])

    top_scores = [score for score in sorted(total_scores, key=lambda x: x[2], reverse=True) if score[1] not in sus]

    df = pd.DataFrame(top_scores)
    df.columns = ["date", "regular nickname", "wave"]

    overall_df = df.loc(0)[:500]
    overall_df["index"] = list(range(1, len(overall_df) + 1))
    overall_df = overall_df.set_index(keys="index")

    peeps = set()
    condensed_scores = []

    for top_score in top_scores:
        if top_score[1] in peeps:
            continue

        condensed_scores.append(top_score)
        peeps.add(top_score[1])

    condensed_df = pd.DataFrame(condensed_scores)
    condensed_df.columns = ["date", "regular nickname", "wave"]
    condensed_df = condensed_df.loc(0)[:100]
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

    tab.dataframe(condensed_df.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=400)
    tab.write("Overall:")
    tab.dataframe(overall_df.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=400)


###############
### breakdown
###############


def compute_breakdown():
    # tab = breakdown_tab
    tab = st

    def get_stratified_counts(results):
        return {lower_strata: sum(higher_strata >= result[2] > lower_strata for result in results) for lower_strata, higher_strata in zip(stratas, stratas[1:])}

    stratified_results = {date: get_stratified_counts(results) for date, results in total_results.items()}
    restratified_results = {strata: [stratified_result.get(strata, 0) for date, stratified_result in stratified_results.items()] for strata in stratas}
    if 100000 in stratas:
        stratas.pop(-1)
    restratified_results.pop(10000, None)

    stratified_plot_data = [
        go.Bar(
            name=name,
            x=list(stratified_results.keys()),
            y=results,
        )
        for name, results in restratified_results.items()
    ]

    for datum, color_ in zip(stratified_plot_data, colors):
        datum.update(marker_color=color_)

    fig = go.Figure(data=stratified_plot_data)
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode="stack", title="Role counts per tournament, courtesy of ObsUK")

    tab.plotly_chart(fig)


###############
### comparison
###############


def compute_comparison():
    # tab = comparison_tab
    tab = st

    tab.title("See rating progression of multiple players")

    top5 = tab.checkbox("Compare 0.16 top5 players?")

    # cf_warriors = ["Milamber33", "Marchombre", "Skrag", "this_guy_with", "AbraSjefen", "IceTae", "Fleshwound"]
    _, condensed_df = get_top_scores_df()

    if top5:
        default_value = list(condensed_df.loc(0)[:4]["regular nickname"])
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

            if len(data) > 2:
                datas.append(data)
                position_datas.append(position_data)

        if datas:
            tab.code("http://thetower.lol?" + urlencode({"compare": users}, doseq=True))

            pd_datas = pd.concat(datas)
            fig = px.line(pd_datas, x="date", y="wave", color="user", markers=True)

            min_ = min(pd_datas.wave)
            max_ = max(pd_datas.wave)

            for color_, strata in zip(colors, stratas):
                if max_ > strata > min_:
                    fig.add_hline(
                        y=strata,
                        line_color=color_,
                        line_dash="dash",
                        opacity=0.4,
                    )
            tab.plotly_chart(fig)

            fig = px.line(pd.concat(position_datas), x="date", y="position", color="user", markers=True)
            tab.plotly_chart(fig)


###############
### sustab
###############


def compute_sus():
    # tab = sus_tab
    tab = st

    tab.title("Sus people")
    tab.write(
        """Sometimes on the leaderboards there are hackers or otherwise suspicious individuals. The system doesn't necessarily manage to detect and flag all of them, so some postprocessing is required. There's no official approval board for this, I'm just a guy on discord that tries to analyze results. If you'd like your name rehabilitated, please join the tower discord and talk to us in the tournament channel."""
    )

    tab.write("My discord id is `098799#0707`.")

    tab.write("Currently, sus people are:")
    tab.write(sorted(sus))


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
