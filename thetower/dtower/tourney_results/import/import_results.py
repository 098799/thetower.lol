#!/tourney/tourney_venv/bin/python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


import datetime
import subprocess
import time
from glob import glob

from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.constants import champ, leagues, us_to_jim
from dtower.tourney_results.get_results import get_file_name, get_last_date
from dtower.tourney_results.models import TourneyResult

while True:
    for league in leagues:
        print(f"{datetime.datetime.now()} Trying to upload results for {league=} and {get_last_date()=}")

        current_datetime = get_last_date()

        if "T" in current_datetime:
            print("Tourney day, continuing...")

            continue  # change me

            if league != champ:
                continue

            current_date = current_datetime.split("T")[0]
        else:
            last_results = TourneyResult.objects.filter(date=get_last_date(), league=league)

            if last_results:
                print("Nothing new")
                continue

            current_date = current_datetime

        print("Something new")
        last_file = sorted(glob(f"/root/tourney/results_cache/{us_to_jim[league]}/{current_date}*"))[-1]

        try:
            with open(last_file, "rb") as infile:
                contents = infile.read()
        except FileNotFoundError:
            print(f"{last_file=} not found, maybe later")
            continue

        print("Creating file object")
        csv_file = SimpleUploadedFile(
            name=get_file_name(),
            content=contents,
            content_type="text/csv",
        )
        print("Creating tourney_result")
        TourneyResult.objects.update_or_create(
            date=current_date,
            league=league,
            defaults=dict(
                result_file=csv_file,
            ),
        )

        if "T" not in current_datetime:
            subprocess.call("systemctl restart streamlit", shell=True)

    time.sleep(3600)
