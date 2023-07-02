# Generated by Django 4.2 on 2023-06-12 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tourney_results", "0014_alter_patchnew_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="role",
            name="wave_bottom",
            field=models.SmallIntegerField(
                choices=[
                    (0, 0),
                    (250, 250),
                    (500, 500),
                    (750, 750),
                    (1000, 1000),
                    (1250, 1250),
                    (1500, 1500),
                    (1750, 1750),
                    (2000, 2000),
                    (2250, 2250),
                    (2500, 2500),
                    (2750, 2750),
                    (3000, 3000),
                    (3500, 3500),
                    (4000, 4000),
                    (4500, 4500),
                    (5000, 5000),
                    (100000, 100000),
                    (1000000, 1000000),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="wave_top",
            field=models.SmallIntegerField(
                choices=[
                    (0, 0),
                    (250, 250),
                    (500, 500),
                    (750, 750),
                    (1000, 1000),
                    (1250, 1250),
                    (1500, 1500),
                    (1750, 1750),
                    (2000, 2000),
                    (2250, 2250),
                    (2500, 2500),
                    (2750, 2750),
                    (3000, 3000),
                    (3500, 3500),
                    (4000, 4000),
                    (4500, 4500),
                    (5000, 5000),
                    (100000, 100000),
                    (1000000, 1000000),
                ]
            ),
        ),
    ]