import datetime
import logging
import os
import re
from pathlib import Path

import pandas as pd
from django.db.models import Q

from dtower.tourney_results.constants import champ, legend, us_to_jim
from dtower.tourney_results.data import get_player_id_lookup, get_sus_ids
from dtower.tourney_results.models import Injection, PromptTemplate, TourneyResult, TourneyRow

logging.basicConfig(level=logging.INFO)


def create_tourney_rows(tourney_result: TourneyResult) -> None:
    """Idempotent function to process tourney result during the csv import process.

    The idea is that:
     - if there are not rows created, create them,
     - if there are already rows created, update all positions at least (positions should never
    be set manually, that doesn't make sense?),
     - if there are things like wave changed, assume people changed this manually from admin.
    """

    csv_path = tourney_result.result_file.path

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        # try other path
        csv_path = csv_path.replace("uploads", "thetower/dtower/uploads")

        df = pd.read_csv(csv_path)

    if df.empty:
        logging.error(f"Empty csv file: {csv_path}")
        return

    if 0 in df.columns:
        df = df.rename(columns={0: "id", 1: "tourney_name", 2: "wave"})
        df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())
        df["avatar"] = df.tourney_name.map(lambda name: int(avatar[0]) if (avatar := re.findall(r"\#avatar=([-\d]+)\${5}", name)) else -1)
        df["relic"] = df.tourney_name.map(lambda name: int(relic[0]) if (relic := re.findall(r"\#avatar=\d+\${5}relic=([-\d]+)", name)) else -1)
        df["tourney_name"] = df.tourney_name.map(lambda name: name.split("#")[0])
    if "player_id" in df.columns:
        df = df.rename(columns={"player_id": "id", "name": "tourney_name", "wave": "wave"})
        df["tourney_name"] = df["tourney_name"].map(lambda x: x.strip())

    positions = calculate_positions(df.id, df.index, df.wave, get_sus_ids())

    df["position"] = positions

    create_data = []

    for _, row in df.iterrows():
        create_data.append(
            dict(
                player_id=row.id,
                result=tourney_result,
                nickname=row.tourney_name,
                wave=row.wave,
                position=row.position,
                avatar_id=row.avatar,
                relic_id=row.relic,
            )
        )

    TourneyRow.objects.bulk_create([TourneyRow(**data) for data in create_data])


def calculate_positions(ids, indexs, waves, sus_ids) -> list[int]:
    positions = []
    current = 0
    borrow = 1

    for id_, idx, wave in zip(ids, indexs, waves):
        if id_ in sus_ids:
            positions.append(-1)
            continue

        if idx - 1 in indexs and wave == waves[idx - 1]:
            borrow += 1
        else:
            current += borrow
            borrow = 1

        positions.append(current)

    return positions


def reposition(tourney_result: TourneyResult) -> None:
    qs = tourney_result.rows.all().order_by("-wave")
    bulk_data = qs.values_list("player_id", "wave")
    indexes = [idx for idx, _ in enumerate(bulk_data)]
    ids = [datum for datum, _ in bulk_data]
    waves = [wave for _, wave in bulk_data]

    positions = calculate_positions(ids, indexes, waves, get_sus_ids())

    bulk_update_data = []

    for index, obj in enumerate(qs):
        obj.position = positions[index]
        bulk_update_data.append(obj)

    TourneyRow.objects.bulk_update(bulk_update_data, ["position"])


def get_summary(last_date):
    def format_previous_summary(summary, date):
        return f"Summary from {date}:\n{summary}"

    from dtower.tourney_results.data import get_tourneys

    logging.info("Collecting ai summary data...")

    qs = TourneyResult.objects.filter(league=legend, date__lte=last_date).order_by("-date")[:10]

    qs_dates = qs.values_list("date", flat=True)

    champ_qs = TourneyResult.objects.filter(~Q(date__in=qs_dates), league=champ, date__lte=last_date).order_by("-date")[:10]

    df1 = get_tourneys(qs, offset=0, limit=50)
    df2 = get_tourneys(champ_qs, offset=0, limit=50)

    df = pd.concat([df1, df2])

    import anthropic

    ranking = ""

    for date, sdf in df.groupby(["date"]):
        bcs = [(bc.name, bc.shortcut) for bc in sdf.iloc[0]["bcs"]]
        ranking += f"Tourney of {date[0].isoformat()}, battle conditions: {bcs}:\n"
        ranking += "\n".join(
            [
                f"{row.position}. {row.real_name} (tourney_name: {row.tourney_name}) - {row.wave}"
                for _, row in sdf[["position", "real_name", "tourney_name", "wave"]].iterrows()
            ]
        )
        ranking += "\n\n"

        top1_message = Injection.objects.last().text

    prompt_template = PromptTemplate.objects.get(id=1).text
    text = prompt_template.format(
        ranking=ranking,
        last_date=last_date,
        top1_message=top1_message,
    )

    logging.info("Starting to generate ai summary...")
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=1.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    }
                ],
            }
        ],
    )

    response = message.content[0].text
    logging.info(f"Ai summary done: {response}")

    return response


def get_time(file_path: Path) -> datetime.datetime:
    return datetime.datetime.strptime(str(file_path.stem), "%Y-%m-%d__%H_%M")


def get_live_df(league):
    home = Path(os.getenv("HOME"))
    league_folder = us_to_jim[league]
    live_path = home / "tourney" / "results_cache" / f"{league_folder}_live"

    all_files = sorted(live_path.glob("*.csv"))
    last_file = all_files[-1]

    last_date = get_time(last_file)

    data = {current_time: pd.read_csv(file) for file in all_files if last_date - (current_time := get_time(file)) < datetime.timedelta(hours=44)}

    for dt, df in data.items():
        df["datetime"] = dt

    if not data:
        raise ValueError("No current data, wait until the tourney day")

    df = pd.concat(data.values())
    df = df.sort_values(["datetime", "wave"], ascending=False)
    df["bracket"] = df.bracket.map(lambda x: x.strip())

    bracket_counts = dict(df.groupby("bracket").player_id.unique().map(lambda player_ids: len(player_ids)))
    fullish_brackets = [bracket for bracket, count in bracket_counts.items() if count >= 28]

    df = df[df.bracket.isin(fullish_brackets)]  # no sniping
    lookup = get_player_id_lookup()
    df["real_name"] = [lookup.get(id, name).strip() for id, name in zip(df.player_id, df.name)]

    df = df[~df.player_id.isin(get_sus_ids())]
    df = df.reset_index(drop=True)

    return df
