
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView

from dtower.tourney_results.views import results_per_tourney, results_per_user

base_patterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url='admin/', permanent=True))
]


urlpatterns = base_patterns

json_patterns = [
    path("<str:league>/results/<str:tourney_date>/", results_per_tourney),
    path("player_id/<str:player_id>/", results_per_user),
]

urlpatterns += json_patterns
