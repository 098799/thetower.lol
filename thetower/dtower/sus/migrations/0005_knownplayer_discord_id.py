# Generated by Django 4.2 on 2023-06-12 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sus", "0004_historicalsusperson_banned_susperson_banned_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="knownplayer",
            name="discord_id",
            field=models.CharField(
                blank=True, help_text="Discord numeric id", max_length=50, null=True
            ),
        ),
    ]