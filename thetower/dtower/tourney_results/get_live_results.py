#!/tourney/tourney_venv/bin/python
import datetime
import os
import time

import requests

weekdays_sat = [5, 6, 0, 1]
weekdays_wed = [2, 3, 4]

wednesday = 2
saturday = 5


import io
import logging

import pandas as pd

logging.basicConfig(level=logging.INFO)


def get_current_time__game_server():
    """Game server runs on utc time, but we don't want to try accessing results until 1 hour after the tourney is done."""
    return datetime.datetime.utcnow() - datetime.timedelta(hours=1)


def get_date_offset() -> int:
    """Figure out how far away from last tourney day current time is."""
    utcnow = get_current_time__game_server()

    if utcnow.weekday() in weekdays_wed:
        offset = utcnow.weekday() - wednesday
    elif utcnow.weekday() in weekdays_sat:
        offset = (utcnow.weekday() - saturday) % 7
    else:
        raise ValueError("wtf")

    return offset


def get_last_date():
    utcnow = get_current_time__game_server()
    offset = get_date_offset()

    last_tourney_day = (utcnow - datetime.timedelta(days=offset)).day
    last_tourney_month = (utcnow - datetime.timedelta(days=offset)).month
    last_tourney_year = (utcnow - datetime.timedelta(days=offset)).year

    return f"{last_tourney_year}-{str(last_tourney_month).zfill(2)}-{str(last_tourney_day).zfill(2)}__{utcnow.hour}_{utcnow.minute}"


def get_file_name():
    return f"{get_last_date()}.csv"


def get_file_path(file_name, league):
    return f"{os.getenv('HOME')}/tourney/results_cache/{league}_live/{file_name}"


def make_request(league):
    base_url = os.getenv("NEW_LEADERBOARD_URL")
    params = {"tier": league, "pass": os.getenv("LEADERBOARD_PASS")}

    csv_response = requests.get(base_url, params=params)
    csv_contents = csv_response.text

    header = "player_id,name,avatar,relic,wave,bracket,tourney_number\n"

    csv_contents = header + csv_contents
    df = pd.read_csv(io.StringIO(csv_contents.strip()))
    df["wave"] = df["wave"].astype(int)
    df = df.sort_values("wave", ascending=False)
    return df


def execute(league):
    date_offset = get_date_offset()
    current_time = get_current_time__game_server()
    current_hour = current_time.hour

    if date_offset > 1 or date_offset == 1 and current_hour > 5:
        logging.info("Skipping cause _not_ tourney day anymore!!")
        return

    file_path = get_file_path(get_file_name(), league)
    df = make_request(league)

    df.to_csv(file_path, index=False)
    logging.info(f"Successfully stored file {file_path}")

    return True


if __name__ == "__main__":
    while True:
        out = execute("Champion")
        time.sleep(1800)
