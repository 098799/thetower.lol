from django.db import migrations


def upgrade(apps, schema_editor):
    PatchNew = apps.get_model("tourney_results", "PatchNew")
    Role = apps.get_model("tourney_results", "Role")

    for role in Role.objects.all():
        role.patch_new = PatchNew.objects.get(version_minor=(role.patch.version_minor if role.patch.version_minor != 0 else 19))
        role.save()


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0009_role_patch_new")]
    operations = [migrations.RunPython(upgrade)]
