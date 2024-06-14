import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from dtower.tourney_results.models import TourneyResult, TourneyRow
from dtower.tourney_results.tourney_utils import create_tourney_rows, reposition


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


@pytest.mark.django_db(True)
def test_import_results__update():
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
    create_tourney_rows(result)

    # when
    TourneyRow.objects.filter(
        result=result,
        player_id="6D221A1DA7174B6E",
        nickname="GrimLord",
    ).update(
        wave=3360,  # different from the file
        position=2,  # different from the file
    )
    reposition(result)

    # then
    assert TourneyRow.objects.get(player_id="6D221A1DA7174B6E").wave == 3360  # not updated
    assert TourneyRow.objects.get(player_id="6D221A1DA7174B6E").position == 1  # updated
