import datetime
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import migrations

from dtower.tourney_results.constants import champ, data_folder_name_mapping


def upgrade(apps, schema_editor):
    Role = apps.get_model("tourney_results", "Role")
    Patch = apps.get_model("tourney_results", "Patch")

    patch_015 = Patch.objects.create(
        version_minor=15,
        start_date=datetime.datetime(2020, 9, 7),
        end_date=datetime.datetime(2022, 10, 29),
    )
    patch_016 = Patch.objects.create(
        version_minor=16,
        start_date=datetime.datetime(2022, 11, 2),
        end_date=datetime.datetime(2023, 2, 22),
    )
    patch_018 = Patch.objects.create(
        version_minor=18,
        start_date=datetime.datetime(2023, 2, 25),
        end_date=datetime.datetime(2024, 2, 25),
    )

    stratas_boundaries_017 = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 100000]
    colors_017 = [
        "#FFFFFF",
        "#992d22",
        "#e390dc",
        "#ff65b8",
        "#d69900",
        "#06d68a",
        "#3970ec",
        "#206c5b",
        "#ff0000",
        "#6dc170",
        "#00ff00",
    ]

    for strata_bottom, strata_top, color in zip(stratas_boundaries_017, stratas_boundaries_017[1:], colors_017):
        Role.objects.create(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_015,
            color=color,
            league=champ,
        )

    for strata_bottom, strata_top, color in zip(stratas_boundaries_017, stratas_boundaries_017[1:], colors_017):
        Role.objects.create(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_016,
            color=color,
            league=champ,
        )

    stratas_boundaries_018 = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 100000]
    colors_018 = [
        "#FFFFFF",
        "#a4daac",
        "#7bff97",
        "#67f543",
        "#19b106",
        "#ffc447",  # "#ff8000",
        "#ff9931",  # "#ff4200",
        "#ff5f23",  # "#ff0000",
        "#ff0000",
        "#88cffc",  # "#89d1ff",
        "#3da8ff",  # "#61b8ff",
        "#2b7df4",  # "#5c8ddb",
        "#0061ff",  # "#3082ff",
        "#05a99d",  # "#00b1a5",
        "#7efdd3",  # "#7fffd4",
        "#ffffff",
    ]

    for strata_bottom, strata_top, color in zip(stratas_boundaries_018, stratas_boundaries_018[1:], colors_018):
        Role.objects.create(
            wave_bottom=strata_bottom,
            wave_top=strata_top,
            patch=patch_018,
            color=color,
            league=champ,
        )


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0003_patch_role")]
    operations = [migrations.RunPython(upgrade)]
