import csv
import datetime
from collections import Counter, defaultdict
from glob import glob
from typing import Dict, Optional

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st

from components.constants import Role, date_to_patch, hardcoded_nicknames, patch_to_roles, sus_ids, wave_to_role
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
    ids = df.id.unique()

    mapping: Dict[str, str] = {}

    for id_ in ids:
        if id_ in hardcoded_nicknames:
            mapping[id_] = hardcoded_nicknames[id_]
            continue

        filtered_df = df[df["id"] == id_]
        counter = Counter(filtered_df["tourney_name"])
        mapping[id_] = counter.most_common()[0][0]

    return mapping


def get_row_to_role(df: pd.DataFrame):
    name_roles: Dict[int, Optional[Role]] = {}

    for id_ in df.id.unique():
        for patch, roles in patch_to_roles.items():
            filtered_df = df[(df["id"] == id_) & (df["date"] >= patch.start_date) & (df["date"] <= patch.end_date)]
            wave_roles = sorted(filtered_df["wave_role"], reverse=True)

            if wave_roles:
                for index in filtered_df.index:
                    name_roles[index] = wave_roles[0]

    for index in df.index:
        name_roles[index] = name_roles.get(index)

    df["name_role"] = [role for _, role in sorted(name_roles.items())]
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


# df = load_tourney_results("data")
# breakpoint()
