import subprocess

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from dtower.tourney_results.models import TourneyResult


@receiver(post_delete, sender=TourneyResult)
@receiver(post_save, sender=TourneyResult)
def recalculate_results(sender, instance, *args, **kwargs):
    subprocess.call("systemctl restart streamlit2", shell=True)
    subprocess.call("systemctl restart streamlit", shell=True)
