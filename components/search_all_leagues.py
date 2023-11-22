from components.player_lookup import compute_player_lookup
from dtower.tourney_results.constants import Graph, Options

compute_search_all_leagues = compute_player_lookup


if __name__ == "__main__":
    options = Options(links_toggle=False, default_graph=Graph.last_16.value, average_foreground=True)

    compute_search_all_leagues(None, options, all_leagues=True)
