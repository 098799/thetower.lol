from django.http import JsonResponse

from dtower.sus.models import PlayerId
from dtower.tourney_results.data import get_details, get_tourneys, how_many_results_public_site
from dtower.tourney_results.models import TourneyResult, TourneyRow
from dtower.tourney_results.tourney_utils import get_live_df


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


def last_full_results(request, league):
    position = int(request.GET.get("position", 0))  # default to 0 if not provided
    df = get_live_df(league)

    ldf = df[df.datetime == df.datetime.max()]
    response = [
        {"bracket_id": bracket, "position": int(sdf.sort_values("wave", ascending=False).iloc[position + 1].wave)} for bracket, sdf in ldf.groupby("bracket")
    ]

    return JsonResponse(response, status=200, safe=False)
