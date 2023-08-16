"""Watch out!

You need to supply the csv files in migrations/data folder.

What is required is e.g.:

migrations
├── 0001_initial.py
├── 0002_populate.py
├── data
│   ├── copper
│   │   ├── 2022-09-07.csv

^ where league names are defined by `data_folder_name_mapping` and file names are dates in isoformat.
"""


import datetime
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import migrations

from dtower.tourney_results.constants import data_folder_name_mapping


def upgrade(apps, schema_editor):
    TourneyResult = apps.get_model("tourney_results", "TourneyResult")

    base_path = Path("tourney_results/migrations/data")

    for league_path in base_path.iterdir():
        league_name = data_folder_name_mapping[league_path.parts[-1]]

        for file_path in league_path.iterdir():
            csv_file = SimpleUploadedFile(
                name=file_path.parts[-1],
                content=file_path.read_bytes(),
                content_type="text/csv",
            )

            TourneyResult.objects.get_or_create(
                date=datetime.date.fromisoformat(file_path.stem),
                league=league_name,
                defaults=dict(
                    result_file=csv_file,
                    public=True,
                ),
            )


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0001_initial")]
    # operations = [migrations.RunPython(upgrade)]
    operations = []  # done
