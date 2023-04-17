from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from dtower.tourney_results.models import TourneyResult


@admin.register(TourneyResult)
class SusPersonAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "league",
        "date",
        "result_file",
        "public",
    )

    search_fields = (
        "id",
        "league",
        "date",
        "result_file",
        "public",
    )

    list_filter = ["date", "league", "public"]
