from django.db import migrations


def upgrade(apps, schema_editor):
    from dtower.sus.models import SusPerson

    for sus in SusPerson.objects.all():
        history = sus.history.all()
        created = [hist for hist in history if hist.history_type == "+"]

        sus.created = created[0].history_date
        sus.modified = max([sus_entry.history_date for sus_entry in history])
        sus.save()


class Migration(migrations.Migration):
    dependencies = [("sus", "0012_historicalsusperson_created_and_more")]
    operations = [migrations.RunPython(upgrade)]
