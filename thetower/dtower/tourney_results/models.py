from django.db import models
from simple_history.models import HistoricalRecords

from dtower.tourney_results.constants import leagues_choices


class TourneyResult(models.Model):
    result_file = models.FileField(upload_to="uploads/", blank=False, null=False, help_text="CSV file from discord with results.")
    date = models.DateField(blank=False, null=False, help_text="Date of the tournament")
    league = models.CharField(blank=False, null=False, choices=leagues_choices, help_text="Which league are those results from?", max_length=16)
    public = models.BooleanField(blank=False, null=False, default=False, help_text="Are the results shown to everyone or just to review?")

    history = HistoricalRecords()

    def __str__(self):
        return f"({self.pk}): {self.league} {self.date.isoformat()}"
