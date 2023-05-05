from django.contrib import admin
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin

from dtower.sus.models import KnownPlayer, PlayerId, SusPerson


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


class IdInline(admin.TabularInline):
    model = PlayerId
    verbose_name = "Annotation Pipeline User"
    verbose_name_plural = "Annotation Pipeline Users"


@admin.register(KnownPlayer)
class SusPersonAdmin(SimpleHistoryAdmin):
    def _ids(self, obj):
        return mark_safe("<br>".join(obj.ids.all().values_list("id", flat=True)))

    _ids.short_description = "Ids"

    list_display = ("name", "_ids")
    search_fields = ("name",)
    inlines = (IdInline,)
