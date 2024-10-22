#!/tourney/tourney_venv/bin/python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


import logging
import subprocess
import time
from glob import glob

from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.constants import leagues, us_to_jim
from dtower.tourney_results.get_results import get_file_name, get_last_date
from dtower.tourney_results.models import TourneyResult
from dtower.tourney_results.tourney_utils import create_tourney_rows

logging.basicConfig(level=logging.INFO)

while True:
    for league in ["Legend"] + leagues:
        last_date = get_last_date()

        logging.info(f"Trying to upload results for {league=} and {last_date=}")

        last_results = TourneyResult.objects.filter(date=last_date, league=league)

        if last_results:
            logging.info(f"Nothing new, results are already uploaded for {last_date=}")
            continue

        logging.info("Something new")
        last_files = sorted([file_name for file_name in glob(f"/root/tourney/results_cache/{us_to_jim[league]}/{last_date}*") if "csv_raw" not in file_name])

        if not last_files:
            logging.info("Apparently we're checking the files before the download script could get them, try later.")
            continue

        last_file = last_files[-1]

        try:
            with open(last_file, "rb") as infile:
                contents = infile.read()
        except FileNotFoundError:
            logging.info(f"{last_file=} not found, maybe later")
            continue

        logging.info("Creating file object")
        csv_file = SimpleUploadedFile(
            name=get_file_name(),
            content=contents,
            content_type="text/csv",
        )
        logging.info("Creating tourney_result")
        result, _ = TourneyResult.objects.update_or_create(
            date=last_date,
            league=league,
            defaults=dict(
                result_file=csv_file,
            ),
        )

        create_tourney_rows(result)

        # This is how we invalidate the cache on the hidden version of the site
        # Crude, there should be a better way
        subprocess.call("systemctl restart streamlit", shell=True)

    time.sleep(3600)
