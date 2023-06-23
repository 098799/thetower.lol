import os
import subprocess

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from dtower.tourney_results.constants import champ
from dtower.tourney_results.models import TourneyResult


# @receiver(post_delete, sender=TourneyResult)
@receiver(post_save, sender=TourneyResult)
def recalculate_results(sender, instance, signal, created, update_fields, raw, using, **kwargs):
    if os.getenv("DEBUG") == "true":
        return

    if instance.public == False:
        # subprocess.call("systemctl restart streamlit", shell=True)
        ...
    else:
        if instance.league == champ:
            subprocess.call("systemctl restart streamlit2", shell=True)
            subprocess.call("systemctl restart streamlit", shell=True)
