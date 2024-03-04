import re

import pandas as pd
from django.db import migrations
from tqdm import tqdm


def upgrade(apps, schema_editor):
    TourneyResult = apps.get_model("tourney_results", "TourneyResult")
    TourneyRow = apps.get_model("tourney_results", "TourneyRow")

    for result in tqdm(TourneyResult.objects.all()):
        df = pd.read_csv(result.result_file, header=None)
        df = df.rename(columns={0: "id", 1: "tourney_name", 2: "wave"})
        df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
        df["avatar"] = df.tourney_name.map(lambda name: int(avatar[0]) if (avatar := re.findall(r"\#avatar=([-\d]+)\${5}", name)) else -1)
        df["relic"] = df.tourney_name.map(lambda name: int(relic[0]) if (relic := re.findall(r"\#avatar=\d+\${5}relic=([-\d]+)", name)) else -1)
        df["tourney_name"] = df.tourney_name.map(lambda name: name.split("#")[0])

        for _, row in df.iterrows():
            TourneyRow.objects.create(
                result=result,
                player_id=row.id,
                nickname=row.tourney_name,
                wave=row.wave,
                avatar_id=row.avatar,
                relic_id=row.relic,
            )


class Migration(migrations.Migration):
    dependencies = [("tourney_results", "0022_tourneyrow")]
    operations = [migrations.RunPython(upgrade)]
