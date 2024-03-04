import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.data import create_tourney_rows
from dtower.tourney_results.models import TourneyResult, TourneyRow


@pytest.mark.django_db(True)
def test_import_results():
    with open("tourney_results/tests/2022-12-28_bNVSvSX.csv", "rb") as infile:
        contents = infile.read()

    result = TourneyResult.objects.create(
        result_file=SimpleUploadedFile(
            name="2022-12-28_bNVSvSX.csv",
            content=contents,
            content_type="text/csv",
        ),
        date=datetime.date.fromisoformat("2022-12-28"),
        league="Champion",
        public=True,
    )

    # when
    create_tourney_rows(result)

    # then
    assert TourneyRow.objects.filter(result=result).count() == 200
    assert TourneyRow.objects.filter(result=result, position=6).count() == 2
