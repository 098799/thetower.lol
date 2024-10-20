import logging
import os
import re

import pandas as pd

from dtower.tourney_results.constants import legend
from dtower.tourney_results.data import get_sus_ids
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
    # previous_summaries = "\n\n".join([format_previous_summary(summary, date) for summary, date in qs.values_list("overview", "date")])  # not gonna include it now

    df = get_tourneys(qs, offset=0, limit=50)

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

    rival_nicknames = "\n".join(TourneyRow.objects.filter(player_id="9C2FCA80BB3E1B3F").order_by("result__date").values_list("nickname", flat=True))

    prompt_template = PromptTemplate.objects.get(id=1).text
    text = prompt_template.format(
        ranking=ranking,
        last_date=last_date,
        top1_message=top1_message,
        rival_nicknames=rival_nicknames,
    )

    logging.info("Starting to generate ai summary...")
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
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
