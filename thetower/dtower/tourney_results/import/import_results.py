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

from dtower.tourney_results.constants import leagues, us_to_jim
from dtower.tourney_results.get_results import get_file_name, get_last_date
from dtower.tourney_results.models import TourneyResult

while True:
    for league in leagues:
        last_date = get_last_date()

        print(f"{datetime.datetime.now()} Trying to upload results for {league=} and {last_date=}")

        last_results = TourneyResult.objects.filter(date=last_date, league=league)

        if last_results:
            print(f"Nothing new, results are already uploaded for {last_date=}")
            continue

        print("Something new")
        last_files = sorted(glob(f"/root/tourney/results_cache/{us_to_jim[league]}/{last_date}*"))

        if not last_files:
            print("Apparently we're checking the files before the download script could get them, try later.")
            continue

        last_file = last_files[-1]

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
            date=last_date,
            league=league,
            defaults=dict(
                result_file=csv_file,
            ),
        )

        # This is how we invalidate the cache on the hidden version of the site http://thetower.lol:8502/
        # Crude, there should be a better way
        subprocess.call("systemctl restart streamlit", shell=True)

    time.sleep(3600)
