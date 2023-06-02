#!/tourney/tourney_venv/bin/python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


import datetime
import time

from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.constants import leagues, us_to_jim
from dtower.tourney_results.get_results import get_file_name, get_file_path, get_last_date
from dtower.tourney_results.models import TourneyResult

while True:
    for league in leagues:
        print(f"{datetime.datetime.now()} Trying to upload results for {league=} and {get_last_date()=}")

        if "T" in get_last_date():
            print("Tourney day, continuing...")
            continue

        last_results = TourneyResult.objects.filter(date=get_last_date(), league=league)

        if last_results:
            print("Nothing new")
            continue

        print("Something new")
        file_name = get_file_path(us_to_jim[league])

        try:
            with open(file_name, "rb") as infile:
                contents = infile.read()
        except FileNotFoundError:
            print(f"{file_name=} not found, maybe later")
            continue

        print("Creating file object")
        csv_file = SimpleUploadedFile(
            name=get_file_name(),
            content=contents,
            content_type="text/csv",
        )
        print("Creating tourney_result")
        TourneyResult.objects.update_or_create(
            date=get_last_date(),
            league=league,
            result_file=csv_file,
        )

    time.sleep(3600)
