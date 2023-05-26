from django.db import migrations


def upgrade(apps, schema_editor):
    Patch = apps.get_model("tourney_results", "Patch")
    PatchNew = apps.get_model("tourney_results", "PatchNew")

    for patch in Patch.objects.all():
        PatchNew.objects.create(
            version_minor=patch.version_minor,
            beta=patch.beta,
            start_date=patch.start_date,
            end_date=patch.end_date,
        )


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0007_patchnew")]
    operations = [migrations.RunPython(upgrade)]
