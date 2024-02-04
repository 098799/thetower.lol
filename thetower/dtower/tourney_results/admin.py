import subprocess

from django.contrib import admin
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin

from dtower.sus.models import KnownPlayer
from dtower.tourney_results.constants import champ
from dtower.tourney_results.models import BattleCondition, NameDayWinner, PatchNew, PositionRole, Role, TourneyResult


@admin.action(description="Restart the public app")
def restart_public_app(modeladmin, request, queryset):
    subprocess.call("systemctl restart streamlit2", shell=True)


@admin.action(description="Restart the hidden app instance (thetower.lol:8502)")
def restart_hidden_app(modeladmin, request, queryset):
    subprocess.call("systemctl restart streamlit", shell=True)


@admin.action(description="Restart django")
def restart_django(modeladmin, request, queryset):
    subprocess.call("systemctl restart django", shell=True)


@admin.action(description="Restart discord bot")
def restart_discord_bot(modeladmin, request, queryset):
    subprocess.call("systemctl restart discord_bot", shell=True)


@admin.action(description="Publicize")
def publicize(modeladmin, request, queryset):
    for item in queryset:
        item.public = True
        item.save()
        # queryset.update(public=True)


@admin.register(TourneyResult)
class TourneyResultAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "league",
        "date",
        "_conditions",
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

    list_filter = ["date", "league", "public", "conditions"]

    def _conditions(self, obj):
        return mark_safe("<br>".join([str(condition) for condition in obj.conditions.all()]))

    _conditions.short_description = "Battle Conditions"

    filter_horizontal = ("conditions",)

    actions = [
        publicize,
        restart_public_app,
        restart_hidden_app,
        restart_django,
        restart_discord_bot,
    ]


@admin.register(PatchNew)
class PatchNewAdmin(SimpleHistoryAdmin):
    list_display = (
        "version_minor",
        "version_patch",
        "interim",
        "start_date",
        "end_date",
    )

    search_fields = (
        "version_minor",
        "version_patch",
        "start_date",
        "end_date",
    )


@admin.register(Role)
class RoleAdmin(SimpleHistoryAdmin):
    def _color_preview(self, obj):
        return mark_safe(f"""<div style="width: 120px; height: 40px; background: {obj.color};">&nbsp;</div>""")

    _color_preview.short_description = "Color"

    list_display = (
        "wave_bottom",
        "wave_top",
        "patch",
        "league",
        "_color_preview",
        "color",
    )

    search_fields = (
        "wave_bottom",
        "wave_top",
        "patch",
        "league",
        "color",
    )

    list_filter = ["patch", "wave_bottom", "wave_top", "color", "league"]


@admin.register(PositionRole)
class PositionRoleAdmin(SimpleHistoryAdmin):
    def _color_preview(self, obj):
        return mark_safe(f"""<div style="width: 120px; height: 40px; background: {obj.color};">&nbsp;</div>""")

    _color_preview.short_description = "Color"

    list_display = (
        "position",
        "patch",
        "league",
        "_color_preview",
        "color",
    )

    search_fields = (
        "position",
        "patch",
        "league",
        "color",
    )

    list_filter = ["patch", "position", "color", "league"]


@admin.register(BattleCondition)
class BattleConditionAdmin(SimpleHistoryAdmin):
    list_display = (
        "name",
        "shortcut",
    )

    search_fields = (
        "name",
        "shortcut",
    )


@admin.register(NameDayWinner)
class NameDayWinnerAdmin(SimpleHistoryAdmin):
    list_display = (
        "winner",
        "tourney",
        "winning_nickname",
        "nameday_theme",
    )

    search_fields = (
        "winning_nickname",
        "winner__name",
        "winner__discord_id",
        "nameday_theme",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "winner":
            kwargs["queryset"] = KnownPlayer.objects.filter(approved=True).order_by("name")
        elif db_field.name == "tourney":
            kwargs["queryset"] = TourneyResult.objects.filter(public=True, league=champ).order_by("-date")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
