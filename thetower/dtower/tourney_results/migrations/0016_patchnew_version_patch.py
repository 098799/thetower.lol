# Generated by Django 4.2 on 2023-07-25 15:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourney_results", "0015_alter_role_wave_bottom_alter_role_wave_top"),
    ]

    operations = [
        migrations.AddField(
            model_name="patchnew",
            name="version_patch",
            field=models.SmallIntegerField(
                default=0, help_text="The yy in 0.xx.yy version."
            ),
        ),
    ]
