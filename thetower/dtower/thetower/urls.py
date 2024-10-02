import os

from django.contrib import admin
from django.urls import path

from dtower.sus.views import SusView
from dtower.tourney_results.views import plaintext_results, plaintext_results__champ, results_per_tourney, results_per_user

base_patterns = [path("admin/", admin.site.urls)]


urlpatterns = base_patterns

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

json_patterns = [
    path("<str:league>/results/<str:tourney_date>/", results_per_tourney),
    path("player_id/<str:player_id>/", results_per_user),
]

urlpatterns += json_patterns


sus_patterns = [
    path("sus/", SusView.as_view()),
]

urlpatterns += sus_patterns
