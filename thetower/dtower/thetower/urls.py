import os
from functools import partial

from django.contrib import admin
from django.urls import path

from dtower.tourney_results.constants import champ, copper, gold, league_to_folder, plat, silver
from dtower.tourney_results.views import plaintext_results, plaintext_results__champ

league_switcher = os.environ.get("LEAGUE_SWITCHER")

if league_switcher:
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("<str:league>/text/<str:tourney_date>/", plaintext_results),
        path("<str:league>/text/", plaintext_results),
        path("text/<str:tourney_date>/", plaintext_results__champ),
        path("text/", plaintext_results__champ),
    ]
else:
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("text/<str:tourney_date>/", plaintext_results__champ),
        path("text/", plaintext_results__champ),
    ]
