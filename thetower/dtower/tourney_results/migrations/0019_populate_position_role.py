from django.db import migrations


def upgrade(apps, schema_editor):
    PositionRole = apps.get_model("tourney_results", "PositionRole")
    Patch = apps.get_model("tourney_results", "PatchNew")

    for league in {"Champions", "Copper", "Gold", "Platinum", "Silver"}:
        for patch in Patch.objects.all():
            for position, color in zip(
                [10, 50, 100, 200],
                ["#5555FF", "green", "#807e29", "red"],
            ):
                PositionRole.objects.create(
                    position=position,
                    patch=patch,
                    league=league,
                    color=color,
                )


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0018_positionrole")]
    operations = [migrations.RunPython(upgrade)]
