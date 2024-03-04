from django.db import migrations, models
from tqdm import tqdm

from dtower.sus.models import SusPerson


def populate_positions(apps, schema_editor):
    TourneyResult = apps.get_model("tourney_results", "TourneyResult")
    TourneyRow = apps.get_model("tourney_results", "TourneyRow")

    sus_ids = set(SusPerson.objects.filter(sus=True).values_list("player_id", flat=True))

    for result in tqdm(TourneyResult.objects.all()):
        rows = TourneyRow.objects.filter(result=result)
        rows.order_by("-wave")

        positions = []
        current = 0
        borrow = 1

        index = list(range(len(rows)))

        for i, row in enumerate(rows):
            # for id_, idx, wave in zip(df.id, df.index, df.wave):
            if row.id in sus_ids:
                positions.append(-1)
                continue

            if i - 1 in index and row.wave == rows[i - 1].wave:
                borrow += 1
            else:
                current += borrow
                borrow = 1

            positions.append(current)

        for i, row in enumerate(rows):
            row.position = positions[i]
            row.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tourney_results", "0023_populate_tourney_row"),
    ]

    operations = [
        migrations.AddField(
            model_name="tourneyrow",
            name="position",
            field=models.IntegerField(blank=True, help_text="Position in a given tourney", null=True),
        ),
        migrations.RunPython(populate_positions),
        migrations.AlterField(
            model_name="tourneyrow",
            name="position",
            field=models.IntegerField(help_text="Position in a given tourney"),
        ),
    ]
