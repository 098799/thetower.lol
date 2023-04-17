import datetime
from urllib.parse import urlencode

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from components.constants import Graph, Options, Patch, colors_017, colors_018, id_mapping, patch_016, patch_018, stratas_boundaries, stratas_boundaries_018
from components.data import get_player_list, get_sus_ids, load_tourney_results
from components.formatting import color_position


def compute_player_lookup(df, options: Options):
    sus_ids = get_sus_ids()

    first_choices, all_real_names, all_tourney_names, all_user_ids, last_top_scorer = get_player_list(df)
    player_list = [""] + first_choices + sorted(all_real_names | all_tourney_names) + all_user_ids

    if options.current_player is not None:
        player_list = [options.current_player] + player_list

    user = st.selectbox("Which user would you like to lookup?", player_list)

    if user == "Soelent":
        st.image("towerfans.jpg")

    if not user:
        return

    st.code("http://thetower.lol?" + urlencode({"player": user}, doseq=True))

    if user in (set(first_choices) | all_real_names | all_tourney_names):
        player_df = df[(df.real_name == user) | (df.tourney_name == user)]
    elif user in all_user_ids:
        player_df = df[df.id == id_mapping.get(user, user)]
    else:
        raise ValueError("Incorrect user, don't be a smartass.")

    if len(player_df.id.unique()) >= 2:
        potential_ids = player_df.id.unique().tolist()
        aggreg = player_df.groupby("id").count()
        most_common_id = aggreg[aggreg.tourney_name == aggreg.tourney_name.max()].index[0]
        user_ids = st.multiselect(
            "Since multiple players had the same username, please choose id. If you are confident the same user used multiple ids, you can select multiple. If it's different users, data below won't make much sense",
            potential_ids,
            default=most_common_id,
        )

        if not user_ids:
            return

        player_df = df[df.id.isin(user_ids)]
    else:
        player_df = df[df.id == player_df.iloc[0].id]

    player_df = player_df.sort_values("date", ascending=False)

    real_name = player_df.iloc[0].real_name
    id_ = player_df.iloc[0].id
    current_role_color = player_df.iloc[0].name_role.color

    patches_active = player_df.patch.unique()

    if id_ in sus_ids:
        st.error("This player is considered sus.")

    st.write(
        f"Player <font color='{current_role_color}'>{real_name}</font> has been active in top200 champ during the following patches: {sorted([patch.version_minor for patch in patches_active])}. (0.17 counts as part of 0.16 since no roles were reset back then)",
        unsafe_allow_html=True,
    )

    graph_options = [options.default_graph.value] + [value for value in Graph.__members__.keys() if value != options.default_graph.value]
    patch_col, average_col = st.columns([1, 1])
    patch = patch_col.selectbox("Limit results to a patch? (see side bar to change default)", graph_options)
    rolling_average = average_col.slider("Use rolling average for results from how many tourneys?", min_value=1, max_value=10, value=5)

    if patch.startswith("patch"):
        patch = globals()[patch]

    if isinstance(patch, Patch):
        patch_df = player_df[player_df.patch == patch]

        if patch == patch_018:
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
    tbdf["average"] = tbdf.wave.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)
    tbdf["position_average"] = tbdf.position.rolling(rolling_average, min_periods=1, center=True).mean().astype(int)

    if len(tbdf) > 1:
        graph_position_instead = st.checkbox("Graph position instead")
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not graph_position_instead:
            foreground_kwargs = {}
            background_kwargs = dict(line_dash="dot", line_color="#888", opacity=0.6)

            fig.add_trace(
                go.Scatter(
                    x=tbdf.date,
                    y=tbdf.wave,
                    name="Wave (left axis)",
                    **foreground_kwargs if not options.average_foreground else background_kwargs,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=tbdf.date,
                    y=tbdf.average,
                    name=f"{rolling_average} tourney moving average",
                    **foreground_kwargs if options.average_foreground else background_kwargs,
                )
            )

            min_ = min(tbdf.wave)
            max_ = max(tbdf.wave)

            for color_, strata in zip(colors, stratas):
                if max_ > strata > min_:
                    fig.add_hline(y=strata, line_color=color_, line_dash="dash", opacity=0.4, line_width=3)
        else:
            foreground_kwargs = {}
            background_kwargs = dict(line_dash="dot", line_color="#888", opacity=0.6)

            fig.add_trace(
                go.Scatter(
                    x=tbdf.date,
                    y=tbdf.position,
                    name="Tourney position",
                    **foreground_kwargs if not options.average_foreground else background_kwargs,
                ),
                secondary_y=True,
            )
            fig.add_trace(
                go.Scatter(
                    x=tbdf.date,
                    y=tbdf.position_average,
                    name=f"{rolling_average} tourney moving average",
                    **foreground_kwargs if options.average_foreground else background_kwargs,
                ),
                secondary_y=True,
            )
            fig.update_yaxes(secondary_y=True, range=[200, 0])

        start_16 = patch_016.start_date - datetime.timedelta(days=1)
        start_18 = patch_018.start_date - datetime.timedelta(days=1)

        for start, name in [(start_16, "0.16"), (start_18, "0.18")]:
            if start < tbdf.date.min() - datetime.timedelta(days=2) or start > tbdf.date.max() + datetime.timedelta(days=3):
                continue

            fig.add_vline(x=start, line_width=3, line_dash="dash", line_color="#888", opacity=0.4)
            fig.add_annotation(
                x=start,
                y=tbdf.position.min() if graph_position_instead else (tbdf.wave.max() - 100),
                text=f"Patch {name} start",
                showarrow=True,
                arrowhead=1,
            )

        st.plotly_chart(fig)

    to_be_displayed = (
        tbdf[["date", "tourney_name", "wave", "position", "average"]]
        .style.apply(
            lambda row: [None, f"color: {tbdf[tbdf['date']==row.date].name_role_color.iloc[0]}", None, None, None],
            axis=1,
        )
        .apply(
            lambda row: [None, None, f"color: {tbdf[tbdf['date']==row.date].wave_role_color.iloc[0]}", None, None],
            axis=1,
        )
        .applymap(color_position, subset=["position"])
    )
    st.dataframe(to_be_displayed, use_container_width=True)

    for patch in patches_active[::-1]:
        st.subheader(f"Patch 0.{patch.version_minor if patch.version_minor != 16 else '16-17'}")
        patch_df = player_df[player_df.patch == patch]

        patch_role_color = patch_df.iloc[-1].name_role.color

        max_wave = patch_df.wave.max()
        # avg_wave = patch_df.wave.mean()
        # stdev_wave = patch_df.wave.std()
        max_pos = patch_df.position.min()
        # avg_position = patch_df.position.mean()
        # stdev_position = patch_df.position.std()

        max_data = patch_df[patch_df.wave == max_wave].iloc[0]
        max_pos_data = patch_df[patch_df.position == max_pos].iloc[0]

        st.write(
            f"Max wave for <font color='{patch_role_color}'>{real_name}</font> in champ during patch 0.{patch.version_minor}: <font color='{patch_role_color}'>**{max_wave}**</font>, as {max_data.tourney_name} on {max_data.date}"
            f"<br>Best position for <font color='{patch_role_color}'>{real_name}</font> in champ during patch 0.{patch.version_minor}: <font color='{max_pos_data.position_role_color}'>**{max_pos}**</font>, as {max_pos_data.tourney_name} on {max_pos_data.date}",
            unsafe_allow_html=True,
        )

    st.write(f"User id(s) used: <b>{tbdf.raw_id.unique()}</b>", unsafe_allow_html=True)


if __name__ == "__main__":
    df = load_tourney_results("data")
    compute_player_lookup(df, options=Options(congrats_toggle=True, links_toggle=True, default_graph=Graph("all")))
