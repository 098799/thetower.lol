import logging
import os
import threading

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin
from tqdm import tqdm

from dtower.sus.models import KnownPlayer, PlayerId, Reviewed, SusPerson

BASE_HIDDEN_URL = os.getenv("BASE_HIDDEN_URL")


@admin.register(SusPerson)
class SusPersonAdmin(SimpleHistoryAdmin):
    def _link(self, obj):
        return format_html(f"<a href='{BASE_HIDDEN_URL}player?player={obj.player_id}'>{BASE_HIDDEN_URL}<br>Player<br>?player={obj.player_id}</a>")

    _link.short_description = "link"

    list_display = (
        "_created",
        "notes",
        "player_id",
        "sus",
        "soft_banned",
        "banned",
        "_link",
        "_modified",
    )

    list_editable = (
        "notes",
        "sus",
        "soft_banned",
        "banned",
    )

    search_fields = (
        "player_id",
        "name",
        "notes",
    )

    list_filter = (
        "sus",
        "soft_banned",
        "banned",
        "notes",
    )

    def _created(self, obj):
        return mark_safe(obj.created.strftime("%Y-%m-%d<br>%H:%M:%S"))

    def _modified(self, obj):
        return mark_safe(obj.modified.strftime("%Y-%m-%d<br>%H:%M:%S"))

    def save_model(self, request, obj, form, change):
        player_id = obj.player_id

        obj = super().save_model(request, obj, form, change)
        thread = threading.Thread(target=recalc_all, args=(player_id,))
        thread.start()
        return obj


def recalc_all(player_id):
    from dtower.tourney_results.models import TourneyResult, TourneyRow
    from dtower.tourney_results.tourney_utils import reposition

    all_results = TourneyResult.objects.filter(id__in=TourneyRow.objects.filter(player_id=player_id).values_list("result", flat=True))

    for res in tqdm(all_results):
        reposition(res)

    logging.info(f"Updated {player_id=}")


class IdInline(admin.TabularInline):
    model = PlayerId
    verbose_name = "The Tower Player ID"
    verbose_name_plural = "The Tower Player IDs"


@admin.register(KnownPlayer)
class KnownPlayerAdmin(SimpleHistoryAdmin):
    def _ids(self, obj):
        id_data = obj.ids.all().values_list("id", "primary")

        info = ""

        for id_, primary in id_data:
            primary_string = " primary" if primary else ""
            info += f"{id_}{primary_string}<br>"

        return mark_safe(info)

    _ids.short_description = "Ids"

    list_display = ("name", "approved", "discord_id", "_ids")
    list_editable = ("approved",)
    search_fields = ("name", "discord_id", "ids__id")
    inlines = (IdInline,)

    # def save_model(self, request, obj, form, change):
    #     if form.data.get("ids-0-primary") != "on":
    #         messages.error(request, "The first ID should be primary!")
    #         raise ValueError("The first ID should be primary!")

    #     return super().save_model(request, obj, form, change)


@admin.register(Reviewed)
class ReviewedAdmin(SimpleHistoryAdmin):
    list_display = ("player_id",)
    search_display = ("player_id",)
