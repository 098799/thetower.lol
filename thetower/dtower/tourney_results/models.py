from colorfield.fields import ColorField
from django.db import models
from simple_history.models import HistoricalRecords

from dtower.sus.models import KnownPlayer
from dtower.tourney_results.constants import leagues_choices, wave_border_choices


class PatchNew(models.Model):
    class Meta:
        verbose_name_plural = "patches"

    version_minor = models.SmallIntegerField(blank=False, null=False, help_text="The xx in 0.xx version.")
    version_patch = models.SmallIntegerField(blank=False, null=False, help_text="The yy in 0.xx.yy version.", default=0)
    interim = models.BooleanField(blank=False, null=False, default=False, help_text="Maybe it's just an interim version between the patches?")
    start_date = models.DateField(blank=False, null=False, help_text="First tourney when patch was enforced.")
    end_date = models.DateField(blank=False, null=False, help_text="Last tourney when patch was in use.")

    def __str__(self):
        return f"0.{self.version_minor}.{self.version_patch}{'' if not self.interim else ' interim'}"

    def __gt__(self, other):
        if self.version_minor > other.version_minor:
            return True

        if self.version_minor == other.version_minor:
            if self.version_patch > other.version_patch:
                return True

            if self.version_patch == other.version_patch:
                if not self.interim and other.interim:
                    return True

        return False

    def __ge__(self, other):
        if self.version_minor > other.version_minor:
            return True

        if self.version_minor == other.version_minor:
            if self.version_patch > other.version_patch:
                return True

            if self.version_patch == other.version_patch:
                if self.interim:
                    return True

                if not self.interim and not other.interim:
                    return True

        return False


class Role(models.Model):
    wave_bottom = models.SmallIntegerField(blank=False, null=False, choices=[(wave, wave) for wave in wave_border_choices])
    wave_top = models.SmallIntegerField(blank=False, null=False, choices=[(wave, wave) for wave in wave_border_choices])
    patch = models.ForeignKey(
        PatchNew,
        null=True,
        blank=True,
        related_name="roles",
        on_delete=models.CASCADE,
        help_text="Patch related to a given role.",
    )
    league = models.CharField(
        blank=False,
        null=False,
        choices=leagues_choices,
        help_text="Which league are those results from?",
        max_length=16,
    )
    color = ColorField(max_length=255, null=False, blank=False)

    def __str__(self):
        return f"{self.wave_bottom}:{self.wave_top}, {self.patch}, {self.league}"

    def __gt__(self, other):
        try:
            return self.wave_top > other.wave_top
        except (AttributeError, TypeError):
            return True

    def __ge__(self, other):
        try:
            return self.wave_top >= other.wave_top
        except (AttributeError, TypeError):
            return True


class PositionRole(models.Model):
    position = models.IntegerField(blank=False, null=False, help_text="Position in the tourney.")
    patch = models.ForeignKey(
        PatchNew,
        null=True,
        blank=True,
        related_name="position_roles",
        on_delete=models.CASCADE,
        help_text="Patch related to a given role.",
    )
    league = models.CharField(
        blank=False,
        null=False,
        choices=leagues_choices,
        help_text="Which league are those results from?",
        max_length=16,
    )
    color = ColorField(max_length=255, null=False, blank=False)

    def __str__(self):
        return f"Pos={self.position}, {self.patch}, {self.league}"

    def __gt__(self, other):
        try:
            return self.position > other.position
        except (AttributeError, TypeError):
            return True

    def __ge__(self, other):
        try:
            return self.position >= other.position
        except (AttributeError, TypeError):
            return True


class BattleCondition(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, help_text="Name of the condition.")
    shortcut = models.CharField(max_length=8, null=False, blank=False, help_text="Shortcut of the condition.")

    def __str__(self):
        return f"BC: {self.name} ({self.shortcut})"


class TourneyResult(models.Model):
    result_file = models.FileField(upload_to="uploads/", blank=False, null=False, help_text="CSV file from discord with results.")
    date = models.DateField(blank=False, null=False, help_text="Date of the tournament")
    league = models.CharField(
        blank=False,
        null=False,
        choices=leagues_choices,
        help_text="Which league are those results from?",
        max_length=16,
    )
    public = models.BooleanField(blank=False, null=False, default=False, help_text="Are the results shown to everyone or just to review?")
    conditions = models.ManyToManyField(BattleCondition, related_name="results", help_text="Battle conditions for the tourney.")

    history = HistoricalRecords()

    def __str__(self):
        return f"({self.pk}): {self.league} {self.date.isoformat()}"


class NameDayWinner(models.Model):
    winner = models.ForeignKey(KnownPlayer, null=False, blank=False, related_name="name_day_winners", on_delete=models.CASCADE)
    tourney = models.ForeignKey(TourneyResult, null=False, blank=False, related_name="name_day_winners", on_delete=models.CASCADE)
    winning_nickname = models.CharField(max_length=32, null=False, blank=False, help_text="Tourney name that won that day")
    nameday_theme = models.CharField(max_length=32, null=False, blank=False)


class TourneyRow(models.Model):
    # player = models.ForeignKey(
    #     KnownPlayer, null=False, blank=False, related_name="results", on_delete=models.CASCADE, help_text="Player achieving a given result."
    # )
    player_id = models.CharField(max_length=32, null=False, blank=False, help_text="Player id from The Tower")
    position = models.IntegerField(null=False, blank=False, help_text="Position in a given tourney")
    nickname = models.CharField(max_length=32, null=False, blank=False, help_text="Tourney name")
    wave = models.IntegerField(null=False, blank=False, help_text="Tourney score")
    avatar_id = models.SmallIntegerField(null=True, blank=True, help_text="Avatar id")
    relic_id = models.SmallIntegerField(null=True, blank=True, help_text="Relic id")

    result = models.ForeignKey(TourneyResult, null=False, blank=False, related_name="rows", on_delete=models.CASCADE, help_text="Full results file")

    def __str__(self):
        return f"{self.position} {self.player_id} {self.nickname} {self.wave}"

    history = HistoricalRecords()

    class Meta:
        ordering = ["-result__date", "position"]
