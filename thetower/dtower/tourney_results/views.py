from cachetools import TTLCache, cached
from django.http import HttpResponse

from dtower.tourney_results.data import get_sus_ids, load_tourney_results


@cached(cache=TTLCache(maxsize=10, ttl=600))
def get_data(tourney_date=None):
    df = load_tourney_results("data")
    df = df[~df.id.isin(get_sus_ids())]

    if not tourney_date:
        last_date = df.date.unique()[-1]
    else:
        last_date = tourney_date

    last_df = df[df.date == last_date].reset_index(drop=True)
    return last_df


def plaintext_results(request):
    html = get_data()[["position", "tourney_name", "real_name", "wave"]].to_html()
    return HttpResponse(html)


def plaintext_results__history(request, tourney_date):
    html = get_data(tourney_date)[["position", "tourney_name", "real_name", "wave"]].to_html()
    return HttpResponse(html)
