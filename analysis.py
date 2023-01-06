import cProfile
import csv
import datetime
import pstats
from collections import Counter, defaultdict
from functools import lru_cache
from glob import glob

import pandas as pd
import plotly.express as px
import streamlit as st

profiler = cProfile.Profile()
profiler.enable()
result_files = sorted(glob("data/*"))
total_results = {}
new_patch = datetime.datetime.fromisoformat("2022-11-02").date()


for result_file in result_files:
    tourney_results = []

    with open(result_file, "r") as infile:
        file = csv.reader(infile)
        contents = [line for line in file]

    for id_, raw_name, raw_wave in contents:
        name = raw_name.strip()
        wave = int(raw_wave.strip())
        tourney_results.append((id_, name, wave))

    result_date = datetime.datetime.fromisoformat(result_file.split("/")[1].split(".")[0]).date()
    total_results[result_date] = tourney_results


results_by_id = defaultdict(list)

for tourney_name, results in total_results.items():
    for id_, name, wave in results:
        results_by_id[id_].append((tourney_name, name, wave))


pd.set_option("display.max_rows", None)


@lru_cache(maxsize=None)
def get_data_by_nickname(nickname):
    ids = []

    for id_, results in results_by_id.items():
        names = {name for _, name, _ in results}

        if nickname in names:
            ids.append((id_, results))

    return ids


special_data = {
    "508E64777E74593A": "Davroar",
    "3AF60D885181322C": "Skye",
    "2319505BE01FA063": "Peach",
    "D2E91B297D898157": "PerkMasterDayox",
    "BE82DF9283461C75": "periodic table guy",
    "9C0FFCDC9EC303DB": "Brianator",
    "B9ADDEEDC5E85D1B": "Blaze",
    "3E5F96B750CEE6C4": "NanaSeiYuri",
    "8BD9973232D2CB4B": "...this guy with the green discord pic",
    "9DDCD4902FE1A201": "TJ the weird lines lollipop",
    "33540FD38D7F3B6B": "Helasus23",
    "ECC7934F0D89CFDD": "Dr. Soelent",
    "CB5E6220889629A4": "Skraggle Rock",
}
rev_special_data = {value: key for key, value in special_data.items()}


pretty_results = [pd.DataFrame(results) for name, results in total_results.items()]


@lru_cache(maxsize=None)
def get_majority_name(nickname):
    data = get_data_by_nickname(nickname)
    longest_datum = sorted(data, key=lambda datum: len(datum))[0][1]
    counter = Counter([nickname for _, nickname, _ in longest_datum])
    return counter.most_common()[0][0]


@lru_cache(maxsize=None)
def get_real_nickname(id_, nickname):
    return special_data.get(id_, get_majority_name(nickname))


def translate_results(results):
    def translate_single(result, results):
        nickname = get_real_nickname(result[0], result[1])
        return result[0], result[1], nickname if nickname != result[1] else "", result[2]

    return [translate_single(result, results) for result in results]


tab1, tab2, comparison, tab3 = st.tabs(["Tourney results", "Player lookup", "Player comparison", "Top scores"])


###############
### tourney results
###############

tourney_file_name = tab1.selectbox("Select tournament:", sorted(total_results.keys(), reverse=True))


last_results = pd.DataFrame(translate_results(total_results[tourney_file_name]))
last_results.columns = ["id", "tourney name", "real name", "wave"]

tab1.title("The Tower tourney results")
tab1.dataframe(last_results, use_container_width=True, height=800)


###############
### player lookup
###############

player_list = ["Skye"] + sorted({result for tourney_file in total_results.values() for _, result, _ in tourney_file} | set(special_data.values()))
user = tab2.selectbox("Which user would you like to lookup?", player_list)


def get_detail_data(user):
    if user_id := rev_special_data.get(user):
        user_data = results_by_id[user_id]
        real_username = user
    else:
        user_id, user_data = sorted(get_data_by_nickname(user), key=lambda datum: len(datum[1]))[-1]
        real_username = get_real_nickname(user_id, user)

    data = pd.DataFrame(user_data[::-1])
    data.columns = ["date", "id", "wave"]
    return real_username, user_id, data


real_username, user_id, data = get_detail_data(user)
max_wave_data = data[data["wave"] == data["wave"].max()]

data_new = data[data["date"] > new_patch]
max_wave_data_new = data_new[data_new["wave"] == data_new["wave"].max()]
mean_wave = data_new["wave"].mean()
std_wave = data_new["wave"].std()

last_5_data = data.loc(0)[:4]
mean_wave_last = last_5_data["wave"].mean()
std_wave_last = last_5_data["wave"].std()

if not max_wave_data_new.empty:
    tab2.write(
        f"Max wave for {real_username} in champ _since 0.16_: **{int(max_wave_data_new.wave)}**, as {list(max_wave_data_new.id)[0]} on {list(max_wave_data_new.date)[0]}"
    )
    tab2.write(f"Average wave for {real_username} in champ _since 0.16_: **{round(mean_wave, 2)}** with the standard deviation of {round(std_wave, 2)}")

if not last_5_data.empty:
    tab2.write(
        f"Average wave for {real_username} in champ for the last 5 tournaments: **{round(mean_wave_last, 2)}** with the standard deviation of {round(std_wave_last, 2)}"
    )
tab2.write(f"Max wave for {real_username} in champ: **{int(max_wave_data.wave)}**, as {list(max_wave_data.id)[0]} on {list(max_wave_data.date)[0]}")
tab2.write(f"User Id used: {user_id}")


fig = px.line(data_new, x="date", y="wave")
tab2.plotly_chart(fig)

tab2.dataframe(data, use_container_width=True, height=600)


with tab2.expander("Debug log..."):
    st.write(get_data_by_nickname(user))


###############
### top scores
###############

tab3.title("Top tournament scores")
tab3.write("This tab only collects data from 0.16 onwards. I tried to manually remove some sus scores, please let me know on discord if there's anything left.")


total_scores = []

for tourney_date, tourney_results in total_results.items():
    if tourney_date <= new_patch:
        continue

    for score in tourney_results:
        total_scores.append([tourney_date, get_real_nickname(score[0], score[1]), score[2]])


sus = {"Kehtimmy", "Chronic", "joeljj", "WillBravo7", "Kehtimmy", "legionair", "EEnton", "aaa", "Naiqey"}


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
tab3.dataframe(condensed_df, use_container_width=True, height=400)
tab3.write("Overall:")
tab3.dataframe(overall_df, use_container_width=True, height=400)


###############
### comparison
###############

comparison.title("See rating progression of multiple players")

top5 = comparison.checkbox("Compare 0.16 top5 players?")
users = comparison.multiselect("Which players to compare?", player_list, default=list(condensed_df.loc(0)[:4]["regular nickname"]) if top5 else [])

if users:
    datas = []
    for user in users:
        real_username, user_id, data = get_detail_data(user)
        data["user"] = [real_username] * len(data)
        data = data[data["date"] > new_patch]
        datas.append(data)

    fig = px.line(pd.concat(datas), x="date", y="wave", color="user")
    comparison.plotly_chart(fig)

profiler.disable()
stats = pstats.Stats(profiler).sort_stats("cumtime")
stats.print_stats()
