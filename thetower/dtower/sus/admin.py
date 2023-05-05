from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from dtower.sus.models import SusPerson


@admin.register(SusPerson)
class SusPersonAdmin(SimpleHistoryAdmin):
    list_display = (
        "player_id",
        "name",
        "notes",
        "sus",
    )

    list_editable = (
        "notes",
        "sus",
    )

    search_fields = (
        "player_id",
        "name",
        "notes",
    )

    list_filter = ("sus",)
