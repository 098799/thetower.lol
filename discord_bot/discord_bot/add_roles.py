import asyncio
import datetime
import logging
from collections import defaultdict
from math import ceil

import discord
from asgiref.sync import sync_to_async

from discord_bot import const
from discord_bot.util import get_all_members, get_tower, role_id_to_position
from dtower.sus.models import KnownPlayer, PlayerId, SusPerson
from dtower.tourney_results.constants import champ, copper, gold, leagues, legend, plat, silver
from dtower.tourney_results.data import get_results_for_patch, get_tourneys
from dtower.tourney_results.models import PatchNew as Patch

event_starts = datetime.date(2023, 11, 28)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


lower_roles = {
    copper: [1, const.copper500_id],
    silver: [50, const.silver500_id],
    gold: [100, const.gold500_id],
    plat: [250, const.plat500_id],
    champ: [500, const.champ500_id],
}


async def handle_adding(
    client: discord.Client,
    limit: int | None,
    discord_ids: list[int] | None = None,
    channel: discord.TextChannel | None = None,
    debug_channel: discord.TextChannel | None = None,
    verbose: bool | None = None,
) -> None:
    discord_id_kwargs = {} if discord_ids is None else {"discord_id__in": discord_ids}

    skipped = 0
    unchanged = defaultdict(list)
    changed = defaultdict(list)

    if debug_channel is None:
        debug_channel = channel

    players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False, **discord_id_kwargs)

    if verbose:
        await channel.send(f"Starting the processing of {players.count() if not limit else limit} users... :rocket:")

    patch = sorted(await sync_to_async(Patch.objects.all, thread_sensitive=True)())[-1]

    logging.info("loading dfs")

    dfs = {}

    dfs[leagues[0]] = get_tourneys(get_results_for_patch(patch=patch, league=leagues[0]), limit=2000)  # legend goes up to 2k

    if verbose:
        await debug_channel.send(f"Loaded legends tourney data of {len(dfs[leagues[0]])} rows")

    for league in leagues[1:]:
        dfs[league] = get_tourneys(get_results_for_patch(patch=patch, league=league), limit=20000)

        if verbose:
            await debug_channel.send(f"Loaded {league} tourney data of {len(dfs[league])} rows")

        await asyncio.sleep(0)

    sus_ids = {item.player_id for item in await sync_to_async(SusPerson.objects.filter, thread_sensitive=True)(sus=True)}
    dfs = {league: df[~df.id.isin(sus_ids)] for league, df in dfs.items()}
    logging.info("loaded dfs")

    tower = await get_tower(client)

    logging.info("fetching roles")
    roles = await tower.fetch_roles()
    position_roles = await filter_roles(roles, role_id_to_position)
    wave_roles_by_league = {league: await filter_roles(roles, {role_id: wave_bottom}) for league, (wave_bottom, role_id) in lower_roles.items()}
    wave_roles = [role for role_data in wave_roles_by_league.values() for role in role_data.values()]
    logging.info("fetched roles")

    logging.info("getting all members")
    members = await get_all_members(client)
    logging.info("got all members")

    if verbose:
        await debug_channel.send(f"Fetched all discord members {len(members)=}")

    member_lookup = {member.id: member for member in members}

    player_iter = players.order_by("-id")[:limit] if limit else players.order_by("-id")
    player_data = player_iter.values_list("id", "discord_id")
    total = player_iter.count()
    all_ids = await sync_to_async(PlayerId.objects.filter, thread_sensitive=True)(player__in=players)

    # tourneys_champ = await sync_to_async(TourneyResult.objects.filter, thread_sensitive=True)(date__gt=event_starts, league=champ)
    # tourneys_this_event = tourneys_champ.count() % 4 or 4  # 4 tourneys per event
    # dates_this_event = tourneys_champ.order_by("-date").values_list("date", flat=True)[:tourneys_this_event]
    # dates_this_event = tourneys_champ.order_by("-date").values_list("date", flat=True)  # or not?

    ids_by_player = defaultdict(set)

    for id in all_ids:
        ids_by_player[id.player.id].add(id.id)

    i = 0

    logging.info("iterating over players")
    async for player_id, player_discord_id in player_data:
        i += 1

        if i % 100 == 0:
            logging.info(f"Processed {i} players")
            await asyncio.sleep(0)

        if i % 1000 == 0 and verbose:
            await debug_channel.send(f"Processed {i} out of {total} players")

        ids = ids_by_player[player_id]

        discord_player = member_lookup.get(int(player_discord_id))

        if discord_player is None:
            skipped += 1
            continue

        for league in leagues:
            df = dfs[league]
            player_df = df[df["id"].isin(ids)]

            if not player_df.empty:
                if league == legend:
                    role_assigned = await handle_position_league(player_df, position_roles, discord_player, changed, unchanged)

                    if not role_assigned:  # doesn't qualify for legend role but has some results in legends
                        role = wave_roles_by_league[champ][500]
                        other_roles = [other_role for other_role in wave_roles if other_role != role]
                        await add_wave_roles(changed, discord_player, champ, unchanged, 500, role, other_roles)
                        role_assigned = True

                    if role_assigned:
                        for other_role in other_roles:
                            if other_role in discord_player.roles:
                                await discord_player.remove_roles(other_role)

                        break
                else:
                    role_assigned = await handle_wave_league(player_df, wave_roles_by_league, position_roles, discord_player, league, changed, unchanged)

                    if role_assigned:
                        break
        else:
            for role in wave_roles + list(position_roles.values()):
                if role in discord_player.roles:
                    await discord_player.remove_roles(role)
            skipped += 1

        if discord_player is None:
            discord_player = member_lookup.get(int(player_discord_id))

            if discord_player is None:
                continue

        elif discord_player == "unknown":
            break

    logging.info(f"{skipped=}")

    unchanged_summary = {league: len(unchanged_data) for league, unchanged_data in unchanged.items()}

    if verbose:
        await debug_channel.send(f"""Successfully reviewed all players :tada: \n\n{skipped=} (no role eligible), \n{unchanged_summary=}, \n{changed=}.""")
    else:
        total_players = skipped + sum(unchanged_summary.values()) + sum(len(values) for values in changed.values())

        league_data = {league: str(contents) for league, contents, in unchanged_summary.items()}

        for league, contents in changed.items():
            if len(contents):
                league_data[league] += f"+{len(contents)}"

        league_updates = ", ".join(f"{league}: {league_count}" for league, league_count in league_data.items())
        await debug_channel.send(f"""Bot hourly update: total players: {total_players}, {league_updates}""")

    added_roles = [f"{name}: {league}" for league, contents in changed.items() for name, league in contents]

    chunk_by = 10

    try:
        for chunk in range(ceil(len(added_roles) / chunk_by)):
            added_roles_message = "\n".join(added_roles[chunk * chunk_by : (chunk + 1) * chunk_by])
            await channel.send(added_roles_message)

            if channel != debug_channel:
                await debug_channel.send(added_roles_message)

            await asyncio.sleep(1)
    except Exception:
        pass

    logging.info("**********Done**********")


async def filter_roles(roles, role_id_to_wave):
    return {role_id_to_wave[role.id]: role for role in roles if role.id in role_id_to_wave}


async def handle_position_league(
    df,
    position_roles,
    discord_player,
    changed,
    unchanged,
) -> bool:
    logging.debug(f"{discord_player=} {df.position=}")

    if df.sort_values("date", ascending=False).iloc[0].position == 1:  # special logic for the winner
        rightful_role = position_roles[1]

        if rightful_role in discord_player.roles:
            unchanged[legend].append((discord_player, rightful_role))
            return True  # Don't actually do anything if the player already has the role

        for position_role in position_roles.values():
            await discord_player.remove_roles(position_role)

        await discord_player.add_roles(rightful_role)
        logging.info(f"Added champ top1 role to {discord_player=}")
        changed[legend].append((discord_player.name, rightful_role.name))
        return True

    # current_df = df[df["date"].isin(dates_this_event)]
    current_df = df
    best_position_in_event = current_df.position.min() if not current_df.empty else 100000

    for pos, role in sorted(tuple(position_roles.items()))[1:]:
        if best_position_in_event <= pos:
            rightful_role = role

            if rightful_role in discord_player.roles:
                unchanged[legend].append((discord_player, rightful_role))
                return True  # Don't actually do anything if the player already has the role

            for role in [role for role in discord_player.roles if role.id in role_id_to_position]:
                await discord_player.remove_roles(role)

            await discord_player.add_roles(rightful_role)
            logging.info(f"Added {role=} to {discord_player=}")
            changed[legend].append((discord_player.name, rightful_role.name))
            return True
    else:
        for role in [role for role in discord_player.roles if role.id in role_id_to_position]:
            await discord_player.remove_roles(role)

    return False


async def handle_wave_league(df, wave_roles_by_league, position_roles, discord_player, league, changed, unchanged):
    wave_roles = wave_roles_by_league[league]

    for wave_min, role in wave_roles.items():
        qualifies = any(wave >= wave_min for wave in df.wave)

        if not qualifies:  # this only happens if a player has a result in this league, but doesn't qualify. Then we give the role one lower
            league = leagues.index[league] + 1
            wave_roles = wave_roles_by_league[league]
            wave_min, role = list(wave_roles.items())[0]

        other_roles = [other_role for role_data in wave_roles_by_league.values() for other_role in role_data.values() if other_role != role]

        for other_role in other_roles + list(position_roles.values()):
            if other_role in discord_player.roles:
                await discord_player.remove_roles(other_role)

        if role in discord_player.roles:
            unchanged[league].append((discord_player, role))
            return True

        await add_wave_roles(changed, discord_player, league, unchanged, wave_min, role, other_roles)
        return wave_min

    return False


async def add_wave_roles(changed, discord_player, league, unchanged, wave_min, role, other_roles):
    await discord_player.add_roles(role)
    changed[league].append((discord_player.name, f"{league}: {wave_min}"))
    logging.info(f"Added {league=}, {wave_min=} to {discord_player=}")
