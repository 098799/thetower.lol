import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

import csv
import datetime
import re
from collections import Counter, defaultdict
from functools import cache
from glob import glob
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
from django.db.models import Q

from dtower.sus.models import PlayerId, SusPerson
from dtower.tourney_results.constants import (
    champ,
    data_folder_name_mapping,
    how_many_results_debug,
    how_many_results_hidden_site,
    how_many_results_legacy,
    how_many_results_public_site,
    how_many_results_public_site_other,
)
from dtower.tourney_results.formatting import color_position_barebones
from dtower.tourney_results.models import BattleCondition
from dtower.tourney_results.models import PatchNew as Patch
from dtower.tourney_results.models import Role, TourneyResult, TourneyRow


@cache
def get_patches():
    return Patch.objects.all().order_by("start_date")


def date_to_patch(date: datetime.datetime) -> Optional[Patch]:
    for patch in get_patches():
        if date >= patch.start_date and date <= patch.end_date:
            return patch


def wave_to_role_in_patch(roles: list[Role], wave: int) -> Optional[Role]:
    for role in roles:
        if wave >= role.wave_bottom and wave < role.wave_top:
            return role


@cache
def patch_to_roles(league):
    patch_to_roles = defaultdict(list)

    for role in Role.objects.filter(league=league):
        patch_to_roles[role.patch].append(role)

    return patch_to_roles


def wave_to_role(wave: int, patch: Optional[Patch], league: str) -> Optional[Role]:
    if not patch:
        return None

    roles = patch_to_roles(league)[patch]

    if not roles:
        return None

    return wave_to_role_in_patch(roles, wave)


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


def get_player_id_lookup():
    return dict(PlayerId.objects.filter(player__approved=True).values_list("id", "player__name"))


def get_player_id_approved_lookup():
    return dict(PlayerId.objects.filter(player__approved=True).values_list("id", "player__approved"))


def get_id_lookup():
    player_primary_id = {
        name: id_ for id_, name, primary in PlayerId.objects.filter(player__approved=True).values_list("id", "player__name", "primary") if primary
    }
    return {id_: player_primary_id[name] for id_, name in PlayerId.objects.filter(player__approved=True).values_list("id", "player__name")}


def get_id_real_name_mapping(df: pd.DataFrame, lookup: dict[str, str]) -> dict[str, str]:
    def get_most_common(df):
        return Counter(df["tourney_name"]).most_common()[0][0]

    return {id_: lookup.get(id_, get_most_common(group)) for id_, group in df.groupby("id")}


def get_row_to_role(df: pd.DataFrame, league):
    name_roles: dict[int, Optional[Role]] = {}

    for patch, roles in patch_to_roles(league).items():
        patch_start = np.datetime64(patch.start_date)
        patch_end = np.datetime64(patch.end_date)
        id_df = df[(df["date"] >= patch_start) & (df["date"] <= patch_end)]

        for _, filtered_df in id_df.groupby("id"):
            if not filtered_df.empty:
                wave_role = sorted(filtered_df["wave_role"], reverse=True)[0]
                name_roles.update({index: wave_role for index in filtered_df.index})

    df["name_role"] = df.index.map(name_roles.get)
    df["name_role_color"] = df.name_role.map(lambda role: getattr(role, "color", None))
    return df


def _load_tourney_results(
    result_files: list[tuple[str, str, list[BattleCondition]]],
    league=champ,
    result_cutoff: Optional[int] = None,
) -> pd.DataFrame:
    hidden_features = os.environ.get("HIDDEN_FEATURES")
    league_switcher = os.environ.get("LEAGUE_SWITCHER")
    debug = os.environ.get("DEBUG")

    dfs = []

    sus_ids = get_sus_ids()

    load_data_bar = st.progress(0)

    for index, (result_file, date, bcs) in enumerate(result_files, 1):
        df = pd.read_csv(result_file, header=None)

        cutoff = handle_result_cutoff(hidden_features, league, league_switcher, result_cutoff, debug)

        df = df.iloc[:cutoff]

        df.columns = ["id", "tourney_name", "wave"]

        result_date = datetime.date.fromisoformat(date)
        df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
        df["date"] = result_date
        df["bcs"] = [bcs for _ in range(len(df))]

        positions = []
        current = 0
        borrow = 1

        for id_, idx, wave in zip(df.id, df.index, df.wave):
            if id_ in sus_ids:
                positions.append(-1)
                continue

            if idx - 1 in df.index and wave == df.loc[idx - 1, "wave"]:
                borrow += 1
            else:
                current += borrow
                borrow = 1

            positions.append(current)

        df["position"] = positions
        dfs.append(df)

        load_data_bar.progress(index / len(result_files) * 0.5)

    df = pd.concat(dfs)

    df["avatar"] = df.tourney_name.map(lambda name: int(avatar[0]) if (avatar := re.findall(r"\#avatar=([-\d]+)\${5}", name)) else -1)
    df["relic"] = df.tourney_name.map(lambda name: int(relic[0]) if (relic := re.findall(r"\#avatar=\d+\${5}relic=([-\d]+)", name)) else -1)
    df["tourney_name"] = df.tourney_name.map(lambda name: name.split("#")[0])

    df["raw_id"] = df.id
    id_mapping = get_id_lookup()
    df["id"] = df.id.map(lambda id_: id_mapping.get(id_, id_))  # id renormalization

    lookup = get_player_id_lookup()
    id_to_real_name = get_id_real_name_mapping(df, lookup)

    df["verified"] = df.id.map(lambda id_: "✓" if lookup.get(id_) else "")

    load_data_bar.progress(0.6)

    df["real_name"] = df.id.map(lambda id_: id_to_real_name[id_])

    df["patch"] = df.date.map(date_to_patch)
    df["patch_version"] = df.patch.map(lambda x: x.version_minor)

    load_data_bar.progress(0.75)

    df["wave_role"] = [wave_to_role(wave, date_to_patch(date), league) for wave, date in zip(df["wave"], df["date"])]
    df["wave_role_color"] = df.wave_role.map(lambda role: getattr(role, "color", None))

    load_data_bar.progress(0.95)

    df["position_role_color"] = [color_position_barebones(position) for position in df["position"]]
    df = df.reset_index(drop=True)

    load_data_bar.progress(1.0)

    df = get_row_to_role(df, league=league)

    load_data_bar.empty()
    return df


def handle_result_cutoff(hidden_features, league, league_switcher, result_cutoff, debug):
    if result_cutoff:
        cutoff = result_cutoff
    elif not hidden_features:
        if league_switcher:
            cutoff = how_many_results_public_site

            if league != champ:
                cutoff = how_many_results_public_site_other
        else:
            cutoff = how_many_results_legacy

    else:
        cutoff = how_many_results_hidden_site

    if debug:  # watch out, debug for quick iteration
        cutoff = how_many_results_debug

    return cutoff


@st.cache_data
def load_tourney_results(
    folder: str, patch_id: Optional[int] = None, limit_no_results: Optional[int] = None, result_cutoff: Optional[int] = None
) -> pd.DataFrame:
    return load_tourney_results__uncached(folder, patch_id=patch_id, limit_no_results=limit_no_results, result_cutoff=result_cutoff)


def load_tourney_results__uncached(
    folder: str, patch_id: Optional[int] = None, limit_no_results: Optional[int] = None, result_cutoff: Optional[int] = None
) -> pd.DataFrame:
    hidden_features = os.environ.get("HIDDEN_FEATURES")
    additional_filter = {} if hidden_features else dict(public=True)

    if patch_id is not None:
        patch = Patch.objects.get(id=patch_id)
        additional_filter["date__gte"] = patch.start_date
        additional_filter["date__lte"] = patch.end_date

    league = data_folder_name_mapping.get(folder, folder)

    result_files = sorted(
        [
            (
                Path("thetower/dtower") / str(result.result_file),
                result.date.isoformat(),
                result.conditions.all(),
            )
            for result in TourneyResult.objects.filter(league=league, **additional_filter)
        ],
        key=lambda x: x[1],
    )

    if limit_no_results is not None:
        result_files = result_files[-limit_no_results:]

    return _load_tourney_results(result_files, league, result_cutoff=result_cutoff)


def get_player_list(df):
    last_date = df.date.unique()[-1]
    sus_ids = get_sus_ids()
    first_choices = list(df[(df.date == last_date) & ~(df.id.isin(sus_ids))].real_name)
    set_of_first_choices = set(first_choices)
    all_real_names = set(df.real_name.unique()) - set_of_first_choices
    all_tourney_names = set(df.tourney_name.unique())
    all_user_ids = df.raw_id.unique().tolist()
    last_top_scorer = df[(df.date == sorted(df.date.unique())[-1]) & (df.position == 1)].tourney_name.iloc[0]
    return first_choices, all_real_names, all_tourney_names, all_user_ids, last_top_scorer


def get_sus_data():
    hidden_features = os.environ.get("HIDDEN_FEATURES")

    if hidden_features:
        qs = SusPerson.objects.filter(sus=True).values("name", "player_id", "sus", "banned", "notes").order_by("name")
    else:
        qs = SusPerson.objects.filter(sus=True).values("name", "player_id").order_by("name")

    return qs


def get_sus_ids():
    return set(SusPerson.objects.filter(sus=True).values_list("player_id", flat=True))


def get_banned_ids():
    return set(SusPerson.objects.filter(banned=True).values_list("player_id", flat=True))


def get_soft_banned_ids():
    return set(SusPerson.objects.filter(soft_banned=True).values_list("player_id", flat=True))


def get_results_for_patch(patch: Patch, league=champ):
    hidden_features = os.environ.get("HIDDEN_FEATURES")
    public = {"public": True} if not hidden_features else {}
    return TourneyResult.objects.filter(date__gte=patch.start_date, date__lte=patch.end_date, league=league, **public).order_by("-date")


def get_patch_for_result(result: TourneyResult) -> Patch:
    return Patch.objects.get(start_date__lte=result.date, end_date__gte=result.date)


def create_tourney_rows(tourney_result: TourneyResult) -> None:
    """Idempotent function to process tourney result during the csv import process."""

    tourney_result.rows.all().delete()

    sus_ids = get_sus_ids()

    df = pd.read_csv(tourney_result.result_file, header=None)
    df = df.rename(columns={0: "id", 1: "tourney_name", 2: "wave"})
    df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
    df["avatar"] = df.tourney_name.map(lambda name: int(avatar[0]) if (avatar := re.findall(r"\#avatar=([-\d]+)\${5}", name)) else -1)
    df["relic"] = df.tourney_name.map(lambda name: int(relic[0]) if (relic := re.findall(r"\#avatar=\d+\${5}relic=([-\d]+)", name)) else -1)
    df["tourney_name"] = df.tourney_name.map(lambda name: name.split("#")[0])

    positions = []
    current = 0
    borrow = 1

    for id_, idx, wave in zip(df.id, df.index, df.wave):
        if id_ in sus_ids:
            positions.append(-1)
            continue

        if idx - 1 in df.index and wave == df.loc[idx - 1, "wave"]:
            borrow += 1
        else:
            current += borrow
            borrow = 1

        positions.append(current)

    df["position"] = positions

    for _, row in df.iterrows():
        TourneyRow.objects.create(
            result=tourney_result,
            player_id=row.id,
            nickname=row.tourney_name,
            wave=row.wave,
            avatar_id=row.avatar,
            relic_id=row.relic,
            position=row.position,
        )


def get_tourney_result_details(
    tourney_result: TourneyResult,
    offset: int = 0,
    limit: int = how_many_results_public_site,
    filter_sus: bool = True,
) -> pd.DataFrame:
    hidden_features = os.environ.get("HIDDEN_FEATURES")
    upper_limit = offset + limit

    if not hidden_features:
        upper_limit = min(upper_limit, how_many_results_public_site)

    slice_fun = slice(offset, None) if limit is None else slice(offset, upper_limit)

    rows = TourneyRow.objects.filter(result=tourney_result)

    if filter_sus:
        rows = rows.filter(~Q(player_id__in=get_sus_ids()))

    rows = rows.order_by("position")[slice_fun]
    df = pd.DataFrame(rows.values("player_id", "position", "nickname", "wave", "avatar_id", "relic_id"))
    df = df.rename(columns={"player_id": "id", "nickname": "tourney_name", "avatar_id": "avatar", "relic_id": "relic"})

    lookup = get_player_id_lookup()
    approved_lookup = get_player_id_approved_lookup()

    df["real_name"] = [lookup.get(id, name) for id, name in zip(df.id, df.tourney_name)]
    df["verified"] = ["✓" if approved_lookup.get(id) else "" for id, name in zip(df.id, df.tourney_name)]
    df["wave_role"] = [wave_to_role(wave, get_patch_for_result(tourney_result), tourney_result.league) for wave in df["wave"]]
    df["wave_role_color"] = df.wave_role.map(lambda role: getattr(role, "color", None))
    df["date"] = tourney_result.date

    return df


def get_tourneys(tourney_results: list[TourneyResult], offset: int = 0, limit: int = how_many_results_public_site) -> pd.DataFrame:
    return pd.concat([get_tourney_result_details(tourney_result, offset=offset, limit=limit) for tourney_result in tourney_results]).reset_index(drop=True)


if __name__ == "__main__":
    df = get_tourneys(TourneyResult.objects.filter(league=champ).order_by("-date")[:2])
    breakpoint()

    os.environ["LEAGUE_SWITCHER"] = "true"
    os.environ["HIDDEN_FEATURES"] = "true"

    df = load_tourney_results__uncached("data", patch_id=Patch.objects.last().id)
    breakpoint()
    df = df[~df.id.isin(get_sus_ids())]
    sdf = df[df.date.isin(sorted(df.date.unique())[:3])]
    sdf = sdf[sdf.wave > how_many_results_public_site]

    lasts = {}

    for person in sdf.real_name.unique():
        ddf = df[df.real_name == person]
        last = sorted(ddf.date.unique())[-1]
        lasts[person] = last

    breakpoint()


# import cProfile
# import pstats

# pr = cProfile.Profile()
# pr.run("load_tourney_results('data')")

# stats = pstats.Stats(pr)
# stats.sort_stats("cumtime")
# stats.print_stats(50)
