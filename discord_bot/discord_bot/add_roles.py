import logging
from collections import defaultdict
from math import ceil

import discord
from asgiref.sync import sync_to_async
from tqdm import tqdm

from discord_bot.util import get_safe_league_prefix, get_tower, role_only_champ_tourney_roles_check, role_prefix_and_only_tourney_roles_check
from dtower.sus.models import KnownPlayer
from dtower.tourney_results.constants import champ, league_to_folder, leagues
from dtower.tourney_results.data import get_sus_ids, load_tourney_results__uncached
from dtower.tourney_results.models import PatchNew as Patch


async def handle_adding(client, limit, discord_ids=None, channel=None, debug_channel=None, verbose=None):
    discord_id_kwargs = {} if discord_ids is None else {"discord_id__in": discord_ids}

    skipped = 0
    unchanged = defaultdict(list)
    changed = defaultdict(list)

    if debug_channel is None:
        debug_channel = channel

    players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False, **discord_id_kwargs)

    if verbose:
        await channel.send(f"Starting the processing of {players.count() if not limit else limit} users... :rocket:")

    all_leagues = leagues

    patch = await sync_to_async(Patch.objects.get, thread_sensitive=True)(version_minor=21, version_patch=0, interim=False)
    dfs = {league: load_tourney_results__uncached(league_to_folder[league], patch_id=patch.id) for league in all_leagues}

    tower = await get_tower(client)
    roles = await tower.fetch_roles()

    player_iter = players.order_by("-id")[:limit] if limit else players.order_by("-id")

    for player in tqdm(player_iter):
        ids = await sync_to_async(player.ids.all().values_list, thread_sensitive=True)("id", flat=True)
        discord_player = None

        discord_player, skipped = await handle_leagues(
            all_leagues,
            changed,
            dfs,
            discord_player,
            ids,
            channel,
            patch,
            player,
            roles,
            skipped,
            tower,
            unchanged,
            debug_channel,
        )

        if discord_player is None:
            discord_player = await get_member(tower, int(player.discord_id), channel=debug_channel)

            if discord_player is None:
                continue

        elif discord_player == "unknown":
            break

    logging.info(f"{skipped=}")

    unchanged_summary = {league: len(unchanged_data) for league, unchanged_data in unchanged.items()}

    if verbose:
        await channel.send(f"Successfully reviewed all players :tada: \n\n{skipped=} (no role eligible), \n{unchanged_summary=}, \n{changed=}.")
    else:
        # the only thing bot outputs in the continuous mode, should be easy to review in the channel, not exceed the limit of the message etc.
        added_roles = [f"{name}: {league}" for league, contents in changed.items() for name, league in contents]

        chunk_by = 10

        for chunk in range(ceil(len(added_roles) / chunk_by)):
            added_roles_message = "\n".join(added_roles[chunk * chunk_by : (chunk + 1) * chunk_by])
            await channel.send(added_roles_message)

            if channel != debug_channel:
                await debug_channel.send(added_roles_message)

    logging.info("**********Done**********")


async def get_member(guild, discord_id, channel=None):
    try:
        return await guild.fetch_member(discord_id)
    except discord.errors.NotFound:
        logging.info(f"Failed to fetch {discord_id=}")

        if channel:
            qs = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(discord_id=discord_id)
            await sync_to_async(qs.update, thread_sensitive=True)(approved=False)
            await channel.send(f"User with {discord_id=} is not found, marked as unapproved :warning:")


async def get_position_roles(roles):
    filtered_roles = [role for role in roles if await role_only_champ_tourney_roles_check(role)]
    return dict(sorted([(int(role.name.split()[-1]), role) for role in filtered_roles]))


async def get_league_roles(roles, league):
    if league == champ:
        initial = [(int(role.name.split()[-1]), role) for role in roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))]
        only_250 = [item for item in initial if item[0] == 250]  # remove me when others disappear
        return dict(sorted(only_250, reverse=True))

    return dict(
        sorted(
            [(int(role.name.split()[-1]), role) for role in roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))],
            reverse=True,
        ),
    )


async def handle_champ_position_roles(df, player, roles, discord_player, changed, unchanged) -> bool:
    position_roles = await get_position_roles(roles)
    logging.debug(f"{discord_player=} {df.position=}")

    if df.iloc[-1].position == 1:  # special logic for the winner
        rightful_role = position_roles[1]

        if rightful_role in discord_player.roles:
            unchanged[champ].append((discord_player, rightful_role))
            return True  # Don't actually do anything if the player already has the role

        for position_role in position_roles.values():
            await discord_player.remove_roles(position_role)

        await discord_player.add_roles(rightful_role)
        logging.info(f"Added champ top1 role to {discord_player=}")
        changed[champ].append((discord_player.name, rightful_role.name))
        return True

    best_position_in_patch = df.position.min()

    for pos, role in tuple(position_roles.items())[1:]:
        if best_position_in_patch <= pos:
            rightful_role = role

            if rightful_role in discord_player.roles:
                unchanged[champ].append((discord_player, rightful_role))
                return True  # Don't actually do anything if the player already has the role

            for role in [role for role in discord_player.roles if role.name.startswith("Top")]:
                await discord_player.remove_roles(role)

            await discord_player.add_roles(rightful_role)
            logging.info(f"Added {role=} to {discord_player=}")
            changed[champ].append((discord_player.name, rightful_role.name))
            return True

    return False


async def handle_leagues(
    all_leagues,
    changed,
    dfs,
    discord_player,
    ids,
    channel,
    patch,
    player,
    roles,
    skipped,
    tower,
    unchanged,
    debug_channel,
):
    for league in all_leagues:
        league_roles = await get_league_roles(roles, league)
        df = dfs[league]

        df = df[~df.id.isin(get_sus_ids())]
        player_df = df[df["real_name"] == player.name]
        player_df = player_df[player_df["id"].isin(ids)]
        patch_df = player_df[player_df["patch"] == patch]

        if patch_df.empty:
            continue

        wave_bottom = patch_df.iloc[-1].name_role.wave_bottom

        if wave_bottom == 0:
            continue

        if wave_bottom in league_roles:
            rightful_role = league_roles[wave_bottom]
        else:
            rightful_role = league_roles.get(250)
            wave_bottom = 250

        discord_player = await get_member(tower, int(player.discord_id), channel=debug_channel)

        if discord_player is None:
            return None, skipped + 1

        if league == champ:
            await handle_champ_position_roles(patch_df, player, roles, discord_player, changed, unchanged)
            return discord_player, skipped  # don't give out wave role for champ

        current_champ_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))]
        current_champ_waves = [int(role.name.strip().split()[-1]) for role in current_champ_roles]

        await iterate_waves_and_add_roles(
            changed,
            current_champ_roles,
            current_champ_waves,
            discord_player,
            league,
            rightful_role,
            unchanged,
            wave_bottom,
        )

        break

    else:
        skipped += 1
    return discord_player, skipped


async def iterate_waves_and_add_roles(changed, current_champ_roles, current_champ_waves, discord_player, league, rightful_role, unchanged, wave_bottom):
    if all(wave_bottom > wave for wave in current_champ_waves):
        for champ_role in current_champ_roles:
            await discord_player.remove_roles(champ_role)

        await discord_player.add_roles(rightful_role)
        changed[league].append((discord_player.name, rightful_role.name))
        logging.info(f"Added {rightful_role=} to {discord_player=}")

    else:
        unchanged[league].append((discord_player, rightful_role))
