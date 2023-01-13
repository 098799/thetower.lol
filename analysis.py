import datetime
from collections import Counter
from functools import lru_cache
from statistics import mean, stdev
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from hardcoding import hardcoded_nicknames, rev_hardcoded_nicknames, sus
from load_data import load_data

with st.sidebar:
    league = st.radio("Choose league (champ is the supported one)", ("Champ", "Plat"))
    st.write("Experimental tweaks (use at your own peril)")
    links = st.checkbox("Links to users? (will make dataframe ugly)", value=bool(st.experimental_get_query_params().get("links")))

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

if player := query.get("player"):
    tab2, tab1, winners, comparison, tab3, breakdown = st.tabs(
        ["Player lookup", "Tourney results", "Winners graphs", "Player comparison", "Top scores", "Champ breakdown"]
    )
    current_player = player[0]
    compare_players = None
elif compare_players := st.experimental_get_query_params().get("compare"):
    comparison, tab1, winners, tab2, tab3, breakdown = st.tabs(
        ["Player comparison", "Tourney results", "Winners graphs", "Player lookup", "Top scores", "Champ breakdown"]
    )
    current_player = None
else:
    tab1, winners, tab2, comparison, tab3, breakdown = st.tabs(
        ["Tourney results", "Winners graphs", "Player lookup", "Player comparison", "Top scores", "Champ breakdown"]
    )
    current_player = None
    compare_players = None


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


def color_top(wave):
    for strata, color in zip(stratas[::-1], colors[::-1]):
        if wave >= strata:
            return f"color: {color}"


def color(value):
    if value.startswith("+"):
        return "color: green"
    elif value.startswith("-"):
        return "color: red"
    return "color: orange"


###############
### tourney results
###############

stratas = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 10000]
colors = ["#992d22", "#e390dc", "#ff65b8", "#d69900", "#06d68a", "#3970ec", "#206c5b", "#ff0000", "#6dc170", "#00ff00", "#ffffff"]


def is_pb(id_, wave):
    try:
        return wave == max(row[2] for row in results_by_id[id_] if row[0] > new_patch)
    except ValueError:
        return False


tourneys = sorted(total_results.keys(), reverse=True)

tourney_file_name = tab1.selectbox("Select tournament:", tourneys)
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
last_results["diff"] = [previous_res[0] if (previous_res := list(previous_results[previous_results["id"] == id_].wave)) else 0 for id_ in last_results["id"]]
last_results["diff"] = last_results["wave"] - last_results["diff"]
last_results["diff"] = last_results.apply(lambda row: ("+" if row["diff"] >= 0 else "") + str(row["diff"]), axis=1)
last_results["diff"] = last_results.apply(lambda row: row["diff"] if row["diff"] != "+0" else "==", axis=1)
last_results["diff"] = last_results.apply(lambda row: row["diff"] + (" (pb!)" if is_pb(row["id"], row["wave"]) else ""), axis=1)


tab1.title("The Tower tourney results")


def make_url(username):
    return f"<a href='http://116.203.133.96:8501?player={username}&links=true'>{username}</a>"


to_be_displayed = (
    last_results[["pos", "tourney name", "real name", "wave", "diff"]].style.applymap(color, subset=["diff", "pos"]).applymap(color_top, subset=["wave"])
)

if links:
    to_be_displayed = to_be_displayed.format(make_url, subset=["tourney name"]).to_html(escape=False)
    tab1.write(to_be_displayed, unsafe_allow_html=True)
else:
    tab1.dataframe(to_be_displayed, use_container_width=True, height=800)


###############
### winners
###############


def get_winner(results):
    for result in results:
        nickname = get_real_nickname(result[0], result[1])
        if nickname not in sus:
            return nickname


winners_data = [get_winner(results) for results in total_results.values()]
winners_df = pd.DataFrame(tuple(Counter(winners_data).items()))
winners_df.columns = ["name", "count"]
fig = px.pie(winners_df, values="count", names="name", title="Winners of champ, courtesy of Jim")
fig.update_traces(textinfo="value")
winners.plotly_chart(fig)


top_n = winners.slider("How many players to plot?", min_value=1, max_value=200, value=100)
last_n_tournaments = winners.slider("How many past tournaments?", min_value=2, max_value=15, value=10)


current_top_nicknames = [get_real_nickname(row[0], row[1]) for row in total_results[tourneys[0]][:top_n]]
current_top = [row[0] for row in total_results[tourneys[0]][:top_n]]
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

for color, strata in zip(colors[:-1], stratas[:-1]):
    fig.add_hline(
        y=strata,
        line_color=color,
        line_dash="dash",
        opacity=0.4,
    )
for color, strata in zip(["blue", "green", "#664620", "red"], [10, 50, 100, 200]):
    if strata <= top_n:
        fig.add_vline(x=strata - 0.5, line_width=2, line_dash="dash", line_color=color)

winners.plotly_chart(fig)


###############
### player lookup
###############


last_top_scorer = list(total_results.values())[-1][0][1]
player_list = [current_player if current_player else last_top_scorer] + sorted(
    {result for tourney_file in total_results.values() for _, result, _ in tourney_file} | set(hardcoded_nicknames.values())
)
user = tab2.selectbox("Which user would you like to lookup?", player_list)

real_username, user_id, data = get_detail_data(user)
position_data = pd.DataFrame(position_by_id[user_id], columns=["date", "nickname", "position"])

max_wave_data = data[data["wave"] == data["wave"].max()]

data_new = data[data["date"] > new_patch]
position_data_new = position_data[position_data["date"] > new_patch]

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
    tab2.write(f"Max wave for {real_username} in champ _since 0.16_: **{max_wave}**, as {max_id} on {max_date}")
    tab2.write(f"Average wave for {real_username} in champ _since 0.16_: **{round(mean_wave, 2)}** with the standard deviation of {round(std_wave, 2)}")

if not last_5_data.empty:
    tab2.write(
        f"Average wave for {real_username} in champ for the last 5 tournaments: **{round(mean_wave_last, 2)}** with the standard deviation of {round(std_wave_last, 2)}"
    )

max_wave, max_id, max_date = extract_one(max_wave_data)

tab2.write(f"Max wave for {real_username} in champ: **{max_wave}**, as {max_id} on {max_date}")
tab2.write(f"User Id used: {user_id}")
is_data_full = tab2.checkbox("Graph all data? (not just 0.16)")


data_to_use = data if is_data_full else data_new
position_data_to_use = position_data if is_data_full else position_data_new


if len(data_to_use) > 1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=data_to_use.date, y=data_to_use.wave, name="Wave (left axis)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=position_data_to_use.date, y=position_data_to_use.position, name="Tourney position"),
        secondary_y=True,
    )
    fig.update_yaxes(secondary_y=True, range=[0, 200])

    min_ = min(data_new.wave)
    max_ = max(data_new.wave)

    for color, strata in zip(colors, stratas):
        if max_ > strata > min_:
            fig.add_hline(
                y=strata,
                line_color=color,
                line_dash="dash",
                opacity=0.4,
            )
    tab2.plotly_chart(fig)

tab2.dataframe(data.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=600)


with tab2.expander("Debug log..."):
    st.write(get_data_by_nickname(user))


###############
### top scores
###############

tab3.title("Top tournament scores")
tab3.write(
    "This tab only collects data from 0.16 onwards. I tried to manually remove some sus scores, please let me know on discord if there's anything left."
    if league == "Champ"
    else "This data can be shit, as there were a lot of hackers in plat"
)


total_scores = []

for tourney_date, tourney_results in total_results.items():
    if league == "Champ" and tourney_date <= new_patch:
        continue

    for score in tourney_results:
        total_scores.append([tourney_date, get_real_nickname(score[0], score[1]), score[2]])


top_scores = [score for score in sorted(total_scores, key=lambda x: x[2], reverse=True) if score[1] not in sus]

df = pd.DataFrame(top_scores)
df.columns = ["date", "regular nickname", "wave"]


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
overall_df = df.loc(0)[:500]

tab3.write("Counting only highest per person:")


tab3.dataframe(condensed_df.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=400)
tab3.write("Overall:")
tab3.dataframe(overall_df.style.applymap(color_top, subset=["wave"]), use_container_width=True, height=400)


###############
### breakdown
###############


def get_stratified_counts(results):
    return {lower_strata: sum(higher_strata >= result[2] > lower_strata for result in results) for lower_strata, higher_strata in zip(stratas, stratas[1:])}


stratified_results = {date: get_stratified_counts(results) for date, results in total_results.items()}
restratified_results = {strata: [stratified_result.get(strata, 0) for date, stratified_result in stratified_results.items()] for strata in stratas}
stratas.pop(-1)
restratified_results.pop(10000)

stratified_plot_data = [
    go.Bar(
        name=name,
        x=list(stratified_results.keys()),
        y=results,
    )
    for name, results in restratified_results.items()
]

for datum, color in zip(stratified_plot_data, colors):
    datum.update(marker_color=color)

fig = go.Figure(data=stratified_plot_data)
fig.update_traces(opacity=0.8)
fig.update_layout(barmode="stack", title="Role counts per tournament, courtesy of ObsUK")

breakdown.plotly_chart(fig)


###############
### comparison
###############

comparison.title("See rating progression of multiple players")

top5 = comparison.checkbox("Compare 0.16 top5 players?")

cf_warriors = ["Milamber33", "Marchombre", "Skrag", "this_guy_with", "AbraSjefen", "IceTae", "Fleshwound"]

if top5:
    default_value = list(condensed_df.loc(0)[:4]["regular nickname"])
elif compare_players:
    default_value = list(compare_players)
else:
    default_value = []

users = comparison.multiselect("Which players to compare?", player_list, default=default_value)

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
        pd_datas = pd.concat(datas)
        fig = px.line(pd_datas, x="date", y="wave", color="user", markers=True)

        min_ = min(pd_datas.wave)
        max_ = max(pd_datas.wave)

        for color, strata in zip(colors, stratas):
            if max_ > strata > min_:
                fig.add_hline(
                    y=strata,
                    line_color=color,
                    line_dash="dash",
                    opacity=0.4,
                )
        comparison.plotly_chart(fig)

        fig = px.line(pd.concat(position_datas), x="date", y="position", color="user", markers=True)
        comparison.plotly_chart(fig)
