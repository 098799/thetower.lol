import datetime
import os
from functools import partial

from cachetools import TTLCache, cached
from django.core.exceptions import BadRequest
from django.http import HttpResponse
from pretty_html_table import build_table

from dtower.tourney_results.constants import champ, league_to_folder
from dtower.tourney_results.data import get_sus_ids, load_tourney_results

cache = TTLCache(maxsize=10, ttl=600)


@cached(cache=cache)
def get_data(league, tourney_date=None):
    os.environ["LEAGUE_SWITCHER"] = "True"

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
