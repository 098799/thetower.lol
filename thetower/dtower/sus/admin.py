from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin

from dtower.sus.models import KnownPlayer, PlayerId, SusPerson


@admin.register(SusPerson)
class SusPersonAdmin(SimpleHistoryAdmin):
    def _link(self, obj):
        return format_html(f"<a href='http://thetower.lol:8502/?player={obj.player_id}'>http://thetower.lol:8502/?player={obj.player_id}</a>")

    _link.short_description = "link"

    list_display = (
        "player_id",
        "name",
        "sus",
        "banned",
        "_link",
        "notes",
    )

    list_editable = (
        "notes",
        "sus",
        "banned",
    )

    search_fields = (
        "player_id",
        "name",
        "notes",
    )

    list_filter = (
        "sus",
        "banned",
        "notes",
    )


class IdInline(admin.TabularInline):
    model = PlayerId
    verbose_name = "Annotation Pipeline User"
    verbose_name_plural = "Annotation Pipeline Users"


@admin.register(KnownPlayer)
class KnownPlayerAdmin(SimpleHistoryAdmin):
    def _ids(self, obj):
        return mark_safe("<br>".join(obj.ids.all().values_list("id", flat=True)))

    _ids.short_description = "Ids"

    list_display = ("name", "_ids")
    search_fields = ("name",)
    inlines = (IdInline,)
