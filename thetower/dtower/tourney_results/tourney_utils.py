import re

import pandas as pd

from dtower.tourney_results.data import get_sus_ids
from dtower.tourney_results.models import TourneyResult, TourneyRow


def create_tourney_rows(tourney_result: TourneyResult) -> None:
    """Idempotent function to process tourney result during the csv import process."""

    tourney_result.rows.all().delete()

    sus_ids = get_sus_ids()

    df = pd.read_csv(tourney_result.result_file, header=None)
    df = df.rename(columns={0: "id", 1: "tourney_name", 2: "wave"})
    df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
    df["avatar"] = df.tourney_name.map(lambda name: int(avatar[0]) if (avatar := re.findall(r"\#avatar=([-\d]+)\${5}", name)) else -1)
    df["relic"] = df.tourney_name.map(lambda name: int(relic[0]) if (relic := re.findall(r"\#avatar=\d+\${5}relic=([-\d]+)", name)) else -1)
    df["tourney_name"] = df.tourney_name.map(lambda name: name.split("#")[0])

    positions = []
    current = 0
    borrow = 1

    for id_, idx, wave in zip(df.id, df.index, df.wave):
        if id_ in sus_ids:
            positions.append(-1)
            continue

        if idx - 1 in df.index and wave == df.loc[idx - 1, "wave"]:
            borrow += 1
        else:
            current += borrow
            borrow = 1

        positions.append(current)

    df["position"] = positions

    for _, row in df.iterrows():
        TourneyRow.objects.create(
            result=tourney_result,
            player_id=row.id,
            nickname=row.tourney_name,
            wave=row.wave,
            avatar_id=row.avatar,
            relic_id=row.relic,
            position=row.position,
        )
