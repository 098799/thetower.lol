import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()


from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.constants import leagues, us_to_jim
from dtower.tourney_results.get_results import get_file_name, get_file_path, get_last_date
from dtower.tourney_results.models import TourneyResult

for league in leagues:
    file_name = get_file_path(us_to_jim[league])

    with open(file_name, "rb") as infile:
        contents = infile.read()
        csv_file = SimpleUploadedFile(
            name=get_file_name(),
            content=contents,
            content_type="text/csv",
        )
        TourneyResult.objects.update_or_create(
            date=get_last_date(),
            league=league,
            result_file=csv_file,
        )
