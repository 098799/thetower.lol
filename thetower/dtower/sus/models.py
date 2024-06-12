import datetime

from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords


class KnownPlayer(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Player's friendly name, e.g. common discord handle")
    discord_id = models.CharField(max_length=50, blank=True, null=True, help_text="Discord numeric id")
    approved = models.BooleanField(blank=False, null=False, default=True, help_text="Has this entry been validated?")

    def __str__(self):
        return f"{self.name} ({self.ids.filter(primary=True).first().id if self.ids.filter(primary=True).first() else ''})"


# class RoleAward(models.Model):
#     player = models.ForeignKey(KnownPlayer, null=False, blank=False, related_name="ids", on_delete=models.CASCADE, help_text="Player")
#     # role = models.ForeignKey(Role, null=False, blank=False, related_name="ids", on_delete=models.CASCADE, help_text="Player")


class PlayerId(models.Model):
    id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
    player = models.ForeignKey(KnownPlayer, null=False, blank=False, related_name="ids", on_delete=models.CASCADE, help_text="Player")
    primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id}"

    def save_base(self, *args, force_insert=False, **kwargs):
        if force_insert and self.primary:
            self.player.ids.filter(~Q(id=self.id), primary=True).update(primary=False)

        return super().save_base(*args, **kwargs)


class SusPerson(models.Model):
    player_id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Player's friendly name, e.g. common discord handle")
    notes = models.TextField(null=True, blank=True, max_length=1000, help_text="Additional comments")
    sus = models.BooleanField(
        null=False, blank=False, default=True, help_text="Is the person sus? if checked, they will be removed from the results on the public website."
    )
    soft_banned = models.BooleanField(null=False, blank=False, default=False, help_text="Soft-banned by Pog. For internal use.")
    banned = models.BooleanField(null=False, blank=False, default=False, help_text="Banned by support. For internal use.")

    created = models.DateTimeField(auto_now_add=datetime.datetime.now, null=False, editable=False, db_index=True)
    modified = models.DateTimeField(auto_now=datetime.datetime.now, null=False, editable=False)

    history = HistoricalRecords()


class Reviewed(models.Model):
    player_id = models.CharField(max_length=32, primary_key=True, help_text="Player id from The Tower, pk")
