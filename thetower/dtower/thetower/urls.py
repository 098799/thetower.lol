import os

from django.contrib import admin
from django.urls import path

from dtower.sus.views import SusView
from dtower.tourney_results.views import plaintext_results, plaintext_results__champ

base_patterns = [path("admin/", admin.site.urls)]


urlpatterns = base_patterns

if os.environ.get("LEAGUE_SWITCHER"):
    league_text_patterns = [
        path("<str:league>/text/<str:tourney_date>/", plaintext_results),
        path("<str:league>/text/", plaintext_results),
    ]
    urlpatterns += league_text_patterns


text_patterns = [
    path("text/<str:tourney_date>/", plaintext_results__champ),
    path("text/", plaintext_results__champ),
]

urlpatterns += text_patterns

sus_patterns = [
    path("sus/", SusView.as_view()),
]

urlpatterns += sus_patterns
