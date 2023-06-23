from django.db import migrations


def upgrade(apps, schema_editor):
    KnownPlayer = apps.get_model("sus", "KnownPlayer")

    KnownPlayer.objects.all().update(approved=True)


class Migration(migrations.Migration):
    dependencies = [("sus", "0006_knownplayer_approved")]
    operations = [migrations.RunPython(upgrade)]
