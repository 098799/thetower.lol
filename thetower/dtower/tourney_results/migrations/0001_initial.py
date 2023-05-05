# Generated by Django 4.2 on 2023-04-17 10:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TourneyResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "result_file",
                    models.FileField(
                        help_text="CSV file from discord with results.",
                        upload_to="uploads/",
                    ),
                ),
                ("date", models.DateField(help_text="Date of the tournament")),
                (
                    "league",
                    models.CharField(
                        choices=[
                            ("Champions", "Champions"),
                            ("Platinum", "Platinum"),
                            ("Gold", "Gold"),
                            ("Silver", "Silver"),
                            ("Copper", "Copper"),
                        ],
                        help_text="Which league are those results from?",
                        max_length=16,
                    ),
                ),
                (
                    "public",
                    models.BooleanField(
                        default=False,
                        help_text="Are the results shown to everyone or just to review?",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HistoricalTourneyResult",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "result_file",
                    models.TextField(
                        help_text="CSV file from discord with results.", max_length=100
                    ),
                ),
                ("date", models.DateField(help_text="Date of the tournament")),
                (
                    "league",
                    models.CharField(
                        choices=[
                            ("Champions", "Champions"),
                            ("Platinum", "Platinum"),
                            ("Gold", "Gold"),
                            ("Silver", "Silver"),
                            ("Copper", "Copper"),
                        ],
                        help_text="Which league are those results from?",
                        max_length=16,
                    ),
                ),
                (
                    "public",
                    models.BooleanField(
                        default=False,
                        help_text="Are the results shown to everyone or just to review?",
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
                "verbose_name": "historical tourney result",
                "verbose_name_plural": "historical tourney results",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]