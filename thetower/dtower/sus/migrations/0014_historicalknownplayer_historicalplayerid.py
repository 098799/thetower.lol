# Generated by Django 5.0.6 on 2024-07-17 06:34

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sus", "0013_populate_create_modified_sus"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalKnownPlayer",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Player's friendly name, e.g. common discord handle",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "discord_id",
                    models.CharField(
                        blank=True,
                        help_text="Discord numeric id",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "approved",
                    models.BooleanField(
                        default=True, help_text="Has this entry been validated?"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical known player",
                "verbose_name_plural": "historical known players",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalPlayerId",
            fields=[
                (
                    "id",
                    models.CharField(
                        db_index=True,
                        help_text="Player id from The Tower, pk",
                        max_length=32,
                    ),
                ),
                ("primary", models.BooleanField(default=False)),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        help_text="Player",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="sus.knownplayer",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical player id",
                "verbose_name_plural": "historical player ids",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
