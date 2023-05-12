from functools import partial

from cachetools import TTLCache, cached
from django.http import HttpResponse
from pretty_html_table import build_table

from dtower.tourney_results.constants import champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results


@cached(cache=TTLCache(maxsize=10, ttl=600))
def get_data(league, tourney_date=None):
    df = load_tourney_results(league)
    df = df[~df.id.isin(get_sus_ids())]

    if not tourney_date:
        last_date = df.date.unique()[-1]
    else:
        last_date = tourney_date

    last_df = df[df.date == last_date].reset_index(drop=True)
    return last_df


def plaintext_results(request, league, tourney_date=None):
    df = get_data(league=league_to_folder[league.title()], tourney_date=tourney_date)[["position", "tourney_name", "real_name", "wave"]]
    return HttpResponse(build_table(df, "blue_light"))


plaintext_results__champ = partial(plaintext_results, league=champ)


# def user_role(request, user):
#     if user == "Skye-8263":
#         user = "Skye"

#     df = get_data()
#     role = df[df.real_name == user].name_role.iloc[0]

#     data = {
#         "user": user,
#         "player_ids": list(PlayerId.objects.filter(player__name=user).values_list("id", flat=True)),
#         "role": {
#             "league": role.league,
#             "wave": role.wave_bottom,
#             "color": role.color,
#         },
#     }

#     return JsonResponse(data)
