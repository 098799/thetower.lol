import csv
import datetime
from collections import Counter, defaultdict
from glob import glob
from typing import Dict, Optional

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st

from components.constants import Role, date_to_patch, hardcoded_nicknames, id_mapping, patch_to_roles, sus_ids, wave_to_role
from components.formatting import color_position_barebones


def load_data(folder):
    result_files = sorted(glob(f"{folder}/*"))
    total_results = {}

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

    position_by_id = defaultdict(list)

    for tourney_name, results in total_results.items():
        for positition, (id_, name, wave) in enumerate(results, 1):
            position_by_id[id_].append((tourney_name, name, positition))

    return total_results, results_by_id, position_by_id


def get_id_real_name_mapping(df: pd.DataFrame) -> Dict[str, str]:
    def get_most_common(df):
        return Counter(df["tourney_name"]).most_common()[0][0]

    return {id_: hardcoded_nicknames.get(id_mapping.get(id_, id_), get_most_common(group)) for id_, group in df.groupby("id")}


def get_row_to_role(df: pd.DataFrame):
    name_roles: Dict[int, Optional[Role]] = {}

    for patch, roles in patch_to_roles.items():
        id_df = df[(df["date"] >= patch.start_date) & (df["date"] <= patch.end_date)]

        for _, filtered_df in id_df.groupby("id"):
            if not filtered_df.empty:
                wave_role = sorted(filtered_df["wave_role"], reverse=True)[0]
                name_roles.update({index: wave_role for index in filtered_df.index})

    df["name_role"] = df.index.map(name_roles.get)
    df["name_role_color"] = df.name_role.map(lambda role: getattr(role, "color", None))
    return df


@st.cache(allow_output_mutation=True)
def load_tourney_results(folder: str) -> pd.DataFrame:
    result_files = sorted(glob(f"{folder}/*"))

    dfs = []

    for result_file in result_files:
        df = pd.read_csv(result_file, header=None)
        df.columns = ["id", "tourney_name", "wave"]

        result_date = datetime.datetime.fromisoformat(result_file.split("/")[-1].split(".")[0]).date()
        df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
        df["date"] = [result_date] * len(df)

        positions = []
        current = 1

        for id_ in df.id:
            if id_ in sus_ids:
                positions.append(-1)
                continue

            positions.append(current)
            current += 1

        df["position"] = positions
        dfs.append(df)

    df = pd.concat(dfs)

    id_to_real_name = get_id_real_name_mapping(df)

    df["raw_id"] = df.id
    df["id"] = df.id.map(lambda id_: id_mapping.get(id_, id_))  # id renormalization

    df["real_name"] = df.id.map(lambda id_: id_to_real_name[id_])
    df["patch"] = df.date.map(date_to_patch)
    df["patch_version"] = df.patch.map(lambda x: x.version_minor)

    df["wave_role"] = [wave_to_role(wave, date_to_patch(date)) for wave, date in zip(df["wave"], df["date"])]
    df["wave_role_color"] = df.wave_role.map(lambda role: getattr(role, "color", None))

    df["position_role_color"] = [color_position_barebones(position) for position in df["position"]]
    df = df.reset_index(drop=True)

    df = get_row_to_role(df)
    return df


@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()


@st.cache(allow_output_mutation=True)
def get_player_list(df):
    last_date = df.date.unique()[-1]
    first_choices = list(df[df.date == last_date].real_name)
    set_of_first_choices = set(first_choices)
    all_real_names = set(df.real_name.unique()) - set_of_first_choices
    all_tourney_names = set(df.tourney_name.unique())
    all_user_ids = df.raw_id.unique().tolist()
    last_top_scorer = df[(df.date == sorted(df.date.unique())[-1]) & (df.position == 1)].tourney_name.iloc[0]
    return first_choices, all_real_names, all_tourney_names, all_user_ids, last_top_scorer


if __name__ == "__main__":
    df = load_tourney_results("data")

    for name, group in df.groupby("tourney_name"):
        if len(group.id.unique()) > 1:
            breakpoint()


# import cProfile
# import pstats

# pr = cProfile.Profile()
# pr.run("load_tourney_results('data')")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
