from django.contrib import admin
from dtower.sus.models import SusPerson
from simple_history.admin import SimpleHistoryAdmin


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
