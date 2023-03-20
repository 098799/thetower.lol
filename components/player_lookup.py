import datetime
from urllib.parse import urlencode

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from components.constants import Patch, colors_017, colors_018, patch_015, patch_016, patch_018, stratas_boundaries, stratas_boundaries_018, sus_ids
from components.data import load_tourney_results
from components.formatting import color_position


def compute_player_lookup(df, options=None):
    all_real_names = set(df.real_name.unique())
    all_tourney_names = set(df.tourney_name.unique())
    all_user_ids = df.id.unique().tolist()
    last_top_scorer = df[(df.date == sorted(df.date.unique())[-1]) & (df.position == 1)].tourney_name.iloc[0]
    player_list = [last_top_scorer if options.current_player is None else options.current_player] + sorted(all_real_names | all_tourney_names) + all_user_ids

    user = st.selectbox("Which user would you like to lookup?", player_list)
    st.code("http://thetower.lol?" + urlencode({"player": user}, doseq=True))

    if user in (all_real_names | all_tourney_names):
        player_df = df[(df.real_name == user) | (df.tourney_name == user)]
    elif user in all_user_ids:
        player_df = df[df.id == user]
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
        f"Player <font color='{current_role_color}'>{real_name}</font> has been active in top200 champ during the following patches: {sorted([patch.version_minor for patch in patches_active])}.",
        unsafe_allow_html=True,
    )

    patch = st.selectbox("Limit results to a patch?", ["just last 16 tourneys", "no limit", patch_018, patch_016, patch_015])

    if isinstance(patch, Patch):
        patch_df = player_df[player_df.patch == patch]

        if patch == patch_018:
            colors, stratas = colors_018, stratas_boundaries_018
        else:
            colors, stratas = colors_017, stratas_boundaries
    elif patch == "just last 16 tourneys":
        patch_df = player_df.iloc[:16]
        colors, stratas = colors_018, stratas_boundaries_018
    else:
        patch_df = player_df
        colors, stratas = colors_018, stratas_boundaries_018

    tbdf = patch_df.reset_index(drop=True)

    if len(tbdf) > 1:
        graph_position_instead = st.checkbox("Graph position instead")
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not graph_position_instead:
            fig.add_trace(
                go.Scatter(x=tbdf.date, y=tbdf.wave, name="Wave (left axis)"),
                secondary_y=False,
            )

            min_ = min(tbdf.wave)
            max_ = max(tbdf.wave)

            for color_, strata in zip(colors, stratas):
                if max_ > strata > min_:
                    fig.add_hline(y=strata, line_color=color_, line_dash="dash", opacity=0.4, line_width=3)
        else:
            fig.add_trace(
                go.Scatter(x=tbdf.date, y=tbdf.position, name="Tourney position"),
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
        tbdf[["date", "tourney_name", "wave", "position"]]
        .style.apply(
            lambda row: [None, f"color: {tbdf[tbdf['date']==row.date].name_role_color.iloc[0]}", None, None],
            axis=1,
        )
        .apply(
            lambda row: [None, None, f"color: {tbdf[tbdf['date']==row.date].wave_role_color.iloc[0]}", None],
            axis=1,
        )
        .applymap(color_position, subset=["position"])
    )
    st.dataframe(to_be_displayed, use_container_width=True)

    for patch in patches_active[::-1]:
        st.subheader(f"Patch 0.{patch.version_minor}")
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


if __name__ == "__main__":
    df = load_tourney_results("data")
    compute_player_lookup(df)
