from django.db import models
from simple_history.models import HistoricalRecords


class SusPerson(models.Model):
    player_id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Player's friendly name, e.g. common discord handle")
    notes = models.TextField(null=True, blank=True, max_length=1000, help_text="Additional comments")
    sus = models.BooleanField(null=False, blank=False, default=True, help_text="Is the person sus?")

    history = HistoricalRecords()
