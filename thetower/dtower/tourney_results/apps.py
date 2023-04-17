from django.apps import AppConfig


class TourneyResultsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dtower.tourney_results"

    def ready(self):
        from dtower.tourney_results import signals  # noqa
