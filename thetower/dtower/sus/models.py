from django.db import models
from simple_history.models import HistoricalRecords


class KnownPlayer(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Player's friendly name, e.g. common discord handle")

    def __str__(self):
        return f"{self.name}"


class PlayerId(models.Model):
    id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
    player = models.ForeignKey(KnownPlayer, null=False, blank=False, related_name="ids", on_delete=models.CASCADE, help_text="Player id from The Tower, pk")
    primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id}"


class SusPerson(models.Model):
    player_id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Player's friendly name, e.g. common discord handle")
    notes = models.TextField(null=True, blank=True, max_length=1000, help_text="Additional comments")
    sus = models.BooleanField(null=False, blank=False, default=True, help_text="Is the person sus?")

    history = HistoricalRecords()
