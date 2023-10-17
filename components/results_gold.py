from components.results import compute_results
from components.util import links_toggle
from dtower.tourney_results.constants import Graph, Options, gold, league_to_folder
from dtower.tourney_results.data import load_tourney_results
from dtower.tourney_results.models import PatchNew as Patch

if __name__ == "__main__":
    options = Options(links_toggle=True, default_graph=Graph.last_16.value, average_foreground=True)
    df = load_tourney_results(league_to_folder[gold], patch_id=Patch.objects.last().id)
    compute_results(df, options)
