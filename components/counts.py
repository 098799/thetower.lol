import pandas as pd
import streamlit as st

from dtower.tourney_results.constants import legend
from dtower.tourney_results.models import TourneyResult, TourneyRow


def compute_counts():
    st.header("Wave cutoff required for top X in legend")
    counts_for = [1, 10, 25, 50, 100, 200]
    limit = 300

    check_col, slid_col, _ = st.columns([1, 1, 4])

    show_all = check_col.checkbox("Show all results")

    if show_all:
        counts_for += [300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000]
        limit = 2100

    legend_results = TourneyResult.objects.filter(league=legend, public=True).order_by("-date")

    per_page = 22
    pages = len(legend_results) // per_page
    which_page = slid_col.slider("Select page", 1, pages, 1)

    legend_results = legend_results[(which_page - 1) * per_page : which_page * per_page]

    rows = TourneyRow.objects.filter(result__in=legend_results, position__lt=limit, position__gt=0).order_by("-wave").values("result_id", "wave")

    results = []

    for tourney in legend_results:
        waves = [row["wave"] for row in rows if row["result_id"] == tourney.id]
        result = {
            "date": tourney.date,
            "bcs": "/".join([bc.name for bc in tourney.conditions.all()]),
        }
        result |= {f"Top {count_for}": waves[count_for - 1] if count_for <= len(waves) else 0 for count_for in counts_for}
        results.append(result)

    to_be_displayed = pd.DataFrame(results).sort_values("date", ascending=False).reset_index(drop=True)
    st.dataframe(to_be_displayed, use_container_width=True, height=807, hide_index=True)
