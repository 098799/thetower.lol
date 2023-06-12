import datetime
from collections import defaultdict
from statistics import median, stdev
from urllib.parse import urlencode

import pandas as pd
import plotly.express as px
import streamlit as st

from dtower.tourney_results.constants import Graph, Options, colors_017, colors_018, stratas_boundaries, stratas_boundaries_018
from dtower.tourney_results.data import get_id_lookup, get_patches, get_player_list, get_sus_ids, load_tourney_results
from dtower.tourney_results.formatting import color_top_18, make_url
from dtower.tourney_results.models import PatchNew as Patch


def compute_comparison(df, options: Options):
    sus_ids = get_sus_ids()

    first_choices, all_real_names, all_tourney_names, all_user_ids, _ = get_player_list(df)
    player_list = [""] + first_choices + sorted(all_real_names | all_tourney_names) + all_user_ids

    default_value = list(options.compare_players) if options.compare_players else []
    users = st.multiselect("Which players to compare?", player_list, default=default_value)

    if not users:
        return

    st.code("http://thetower.lol?" + urlencode({"compare": users}, doseq=True))

    datas = []

    patches_options = sorted([patch for patch in get_patches() if patch.version_minor], key=lambda patch: patch.start_date, reverse=True)
    graph_options = [options.default_graph.value] + [
        value for value in list(Graph.__members__.keys()) + patches_options if value != options.default_graph.value
    ]
    patch = st.selectbox("Limit results to a patch? (see side bar to change default)", graph_options)

    id_mapping = get_id_lookup()

    for user in users:
        if user in (set(first_choices) | all_real_names | all_tourney_names):
            player_df = df[(df.real_name == user) | (df.tourney_name == user)]
        elif user in all_user_ids:
            player_df = df[df.id == id_mapping.get(user, user)]
        else:
            raise ValueError("Incorrect user, don't be a smartass.")

        if len(player_df.id.unique()) >= 2:
            aggreg = player_df.groupby("id").count()
            most_common_id = aggreg[aggreg.tourney_name == aggreg.tourney_name.max()].index[0]
            player_df = df[df.id == most_common_id]
        else:
            player_df = df[df.id == player_df.iloc[0].id]

        player_df = player_df.sort_values("date", ascending=False)

        real_name = player_df.iloc[0].real_name
        id_ = player_df.iloc[0].id

        if id_ in sus_ids:
            st.error(f"Player {real_name} is considered sus.")

        if isinstance(patch, Patch):
            patch_df = player_df[player_df.patch == patch]

            if patch.version_minor >= 18:
                colors, stratas = colors_018, stratas_boundaries_018
            else:
                colors, stratas = colors_017, stratas_boundaries
        elif patch == Graph.last_16.value:
            patch_df = player_df[player_df.date.isin(df.date.unique()[-16:])]
            colors, stratas = colors_018, stratas_boundaries_018
        else:
            patch_df = player_df
            colors, stratas = colors_018, stratas_boundaries_018

        tbdf = patch_df.reset_index(drop=True)

        if len(tbdf) >= 2:
            datas.append(tbdf)

    if not datas:
        return

    datas = sorted(datas, key=lambda datum: max(datum.wave), reverse=True)

    summary = pd.DataFrame(
        [
            [
                data.real_name.unique()[0],
                len(data),
                max(data.wave),
                int(round(median(data.wave), 0)),
                int(round(stdev(data.wave), 0)),
                min(data.wave),
            ]
            for data in datas
        ],
        columns=["User", "No. times in champ", "total PB", "Median", "Stdev", "Lowest score on record"],
    )
    summary.set_index(keys="User")

    if options.links_toggle:
        to_be_displayed = summary.style.format(make_url, subset=["User"]).to_html(escape=False)
        st.write(to_be_displayed, unsafe_allow_html=True)
    else:
        st.dataframe(summary, use_container_width=True)

    pd_datas = pd.concat(datas)

    if len(users) == 2 and "Obligatory" in users and any("rival" in user.lower() for user in users):
        mapping = defaultdict(list)

        for _, row in pd_datas.iterrows():
            mapping[row.date].append((row.real_name, row.wave))

        betters = []

        for value in mapping.values():
            if len(value) == 2:
                better = max(value, key=lambda x: x[1])
                betters.append(better)

        st.write(
            f"Oh the great rivalry! Out of all the times they clashed, Obligatory came out ahead {len([better for better in betters if better[0].startswith('Obli')])} times while rival prevailed {len([better for better in betters if better[0].startswith('Char')])} times."
        )
        st.write("May they clash again soon.")

    last_5_tourneys = sorted(pd_datas.date.unique())[-5:][::-1]
    last_results = pd.DataFrame(
        [
            [
                data.real_name.unique()[0],
            ]
            + [wave_serie.iloc[0] if not (wave_serie := data[data.date == date].wave).empty else 0 for date in last_5_tourneys]
            for data in datas
        ],
        columns=["User", *[datetime.datetime.fromtimestamp(int(date) / 1e9).date() for date in last_5_tourneys]],
    )

    last_results = last_results.style.apply(lambda row: [None, *[color_top_18(wave=row[i + 1]) for i in range(len(last_5_tourneys))]], axis=1)

    if options.links_toggle:
        to_be_displayed = last_results.format(make_url, subset=["User"]).to_html(escape=False)
        st.write(to_be_displayed, unsafe_allow_html=True)
    else:
        st.dataframe(last_results, use_container_width=True)

    fig = px.line(pd_datas, x="date", y="wave", color="real_name", markers=True)

    min_ = min(pd_datas.wave)
    max_ = max(pd_datas.wave)

    for color_, strata in zip(colors, stratas):
        if max_ > strata > min_:
            fig.add_hline(
                y=strata,
                line_color=color_,
                line_dash="dash",
                opacity=0.4,
            )

    for index, (start, version_minor, beta) in enumerate(Patch.objects.all().values_list("start_date", "version_minor", "beta")):
        name = f"0.{version_minor}"
        beta = " beta" if beta else ""

        if start < pd_datas.date.min() - datetime.timedelta(days=2) or start > pd_datas.date.max() + datetime.timedelta(days=3):
            continue

        fig.add_vline(x=start, line_width=3, line_dash="dash", line_color="#888", opacity=0.4)
        fig.add_annotation(
            x=start,
            y=tbdf.wave.max() - 300 * (index % 2 + 1),
            text=f"Patch {name}{beta} start",
            showarrow=True,
            arrowhead=1,
        )

    st.plotly_chart(fig)

    fig = px.line(pd_datas, x="date", y="position", color="real_name", markers=True)
    fig.update_yaxes(range=[max(pd_datas.position), min(pd_datas.position)])
    st.plotly_chart(fig)


if __name__ == "__main__":
    df = load_tourney_results("data")
    compute_comparison(df, options=Options(congrats_toggle=True, links_toggle=True, default_graph=Graph("all"), average_foreground=True))
