from django.contrib import admin
from django.urls import path

from dtower.sus.views import SusView
from dtower.tourney_results.views import results_per_tourney, results_per_user

base_patterns = [path("admin/", admin.site.urls)]


urlpatterns = base_patterns

json_patterns = [
    path("<str:league>/results/<str:tourney_date>/", results_per_tourney),
    path("player_id/<str:player_id>/", results_per_user),
]

urlpatterns += json_patterns


sus_patterns = [
    path("sus/", SusView.as_view()),
]

urlpatterns += sus_patterns
