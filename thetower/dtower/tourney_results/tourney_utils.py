import re

import pandas as pd

from dtower.tourney_results.data import get_sus_ids
from dtower.tourney_results.models import TourneyResult, TourneyRow


def create_tourney_rows(tourney_result: TourneyResult) -> None:
    """Idempotent function to process tourney result during the csv import process.

    The idea is that:
     - if there are not rows created, create them,
     - if there are already rows created, update all positions at least (positions should never
    be set manually, that doesn't make sense?),
     - if there are things like wave changed, assume people changed this manually from admin.
    """

    sus_ids = get_sus_ids()

    csv_path = tourney_result.result_file.path

    try:
        df = pd.read_csv(csv_path, header=None)
    except FileNotFoundError:
        # try other path
        csv_path = csv_path.replace("uploads", "thetower/dtower/uploads")

        df = pd.read_csv(csv_path, header=None)

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
        current_qs = TourneyRow.objects.filter(
            player_id=row.id,
            result=tourney_result,
        )

        if current_qs.exists():
            # weird case that shouldn't happen: if there are multiple results for the same id,
            # assume it's an error and needs to be corrected
            if len(current_qs) > 1:
                current_qs.delete()
            else:  # update only position, assume other data might have been changed manually?
                current_qs.update(position=row.position)
        else:
            TourneyRow.objects.create(
                player_id=row.id,
                result=tourney_result,
                nickname=row.tourney_name,
                wave=row.wave,
                avatar_id=row.avatar,
                relic_id=row.relic,
                position=row.position,
            )
