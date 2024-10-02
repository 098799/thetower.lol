import datetime
from functools import partial

from cachetools import TTLCache, cached
from django.core.exceptions import BadRequest
from django.http import HttpResponse, JsonResponse
from pretty_html_table import build_table

from dtower.sus.models import PlayerId, SusPerson
from dtower.tourney_results.constants import champ, league_to_folder
from dtower.tourney_results.data import get_details, get_sus_ids, get_tourneys, how_many_results_public_site, load_tourney_results
from dtower.tourney_results.models import TourneyResult, TourneyRow

cache = TTLCache(maxsize=10, ttl=600)


@cached(cache=cache)
def get_data(league, tourney_date=None):
    df = load_tourney_results(league)
    df = df[~df.id.isin(get_sus_ids())]

    if not tourney_date:
        last_date = df.date.unique()[-1]
    else:
        try:
            last_date = datetime.date.fromisoformat(tourney_date)
        except ValueError:
            raise (BadRequest("Invalid date format"))

    last_df = df[df.date == last_date].reset_index(drop=True)
    return last_df


def plaintext_results(request, league, tourney_date=None):
    df = get_data(league=league_to_folder[league.title()], tourney_date=tourney_date)[["position", "tourney_name", "real_name", "wave"]]
    return HttpResponse(build_table(df, "blue_light"))


plaintext_results__champ = partial(plaintext_results, league=champ)


def results_per_tourney(request, league, tourney_date):
    qs = TourneyResult.objects.filter(league=league.capitalize(), date=tourney_date, public=True)

    if not qs.exists():
        return JsonResponse({}, status=404)

    df = get_tourneys(qs, offset=0, limit=how_many_results_public_site)
    df["wave_role"] = df.wave_role.map(lambda x: x.wave_bottom)
    df["verified"] = df.verified.map(lambda x: int(bool(x)))

    response = [
        {
            "id": row.id,
            "position": row.position,
            "tourney_name": row.tourney_name,
            "real_name": row.real_name,
            "wave": row.wave,
            "avatar": row.avatar,
            "relic": row.relic,
            "date": row.date,
            "league": row.league,
            "verified": row.verified,
            "wave_role": row.wave_role,
            "patch": str(row.patch),
        }
        for _, row in df.iterrows()
    ]

    return JsonResponse(response, status=200, safe=False)


def results_per_user(request, player_id):
    player_ids = PlayerId.objects.filter(id=player_id)
    how_many = int(request.GET.get("how_many", 1000))

    if player_ids:
        player_id = player_ids[0]
        all_player_ids = player_id.player.ids.all().values_list("id", flat=True)
        rows = (
            TourneyRow.objects.select_related("result")
            .filter(
                player_id__in=all_player_ids,
                result__public=True,
                position__gt=0,
            )
            .order_by("-result__date")[:how_many]
        )
    else:
        rows = (
            TourneyRow.objects.select_related("result")
            .filter(
                player_id=player_id,
                result__public=True,
                position__gt=0,
            )
            .order_by("-result__date")[:how_many]
        )

    df = get_details(rows)
    df["wave_role"] = df.wave_role.map(lambda x: x.wave_bottom)
    df["verified"] = df.verified.map(lambda x: int(bool(x)))

    response = [
        {
            "id": row.id,
            "position": row.position,
            "tourney_name": row.tourney_name,
            "real_name": row.real_name,
            "wave": row.wave,
            "avatar": row.avatar,
            "relic": row.relic,
            "date": row.date,
            "league": row.league,
            "verified": row.verified,
            "wave_role": row.wave_role,
            "patch": str(row.patch),
        }
        for _, row in df.iterrows()
    ]

    return JsonResponse(response, status=200, safe=False)
