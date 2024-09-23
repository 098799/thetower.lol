import asyncio
import datetime
import logging
from collections import defaultdict
from math import ceil

from asgiref.sync import sync_to_async

from discord_bot.util import get_all_members, get_safe_league_prefix, get_tower, role_id_to_position, role_prefix_and_only_tourney_roles_check
from dtower.sus.models import KnownPlayer, PlayerId, SusPerson
from dtower.tourney_results.constants import champ, leagues
from dtower.tourney_results.data import get_results_for_patch, get_tourneys
from dtower.tourney_results.models import PatchNew as Patch

event_starts = datetime.date(2023, 11, 28)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    patch = sorted(await sync_to_async(Patch.objects.all, thread_sensitive=True)())[-1]

    logging.info("loading dfs")
    # only limit to at most 4 tourneys? or maybe not?

    dfs = {}

    dfs[leagues[0]] = get_tourneys(get_results_for_patch(patch=patch, league=leagues[0]), limit=2000)  # champ goes up to 2k

    if verbose:
        await debug_channel.send(f"Loaded champ tourney data of {len(dfs[leagues[0]])} rows")

    await asyncio.sleep(0)

    for league in leagues[1:]:
        dfs[league] = get_tourneys(get_results_for_patch(patch=patch, league=league), limit=5000)

        if verbose:
            await debug_channel.send(f"Loaded {league} tourney data of {len(dfs[league])} rows")

        await asyncio.sleep(0)

    # dfs = {
    #     league: get_tourneys(get_results_for_patch(patch=patch, league=league), limit=5000) for league in leagues[1:]
    # } | {  # potentially more to reach everyone who cleared 500 waves
    #     league: get_tourneys(get_results_for_patch(patch=patch, league=league), limit=2000) for league in leagues[:1]  # champ goes up to 2k
    # }
    sus_ids = {item.player_id for item in await sync_to_async(SusPerson.objects.filter, thread_sensitive=True)(sus=True)}
    dfs = {league: df[~df.id.isin(sus_ids)] for league, df in dfs.items()}
    # dfs = {league: get_tourneys(league_to_folder[league], patch_id=patch.id) for league in all_leagues}
    logging.info("loaded dfs")

    tower = await get_tower(client)

    logging.info("fetching roles")
    roles = await tower.fetch_roles()
    league_roles_all = {league: (await get_league_roles(roles, league)) for league in all_leagues}
    position_roles = await get_position_roles(roles)
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

        discord_player, skipped = await handle_leagues(
            all_leagues,
            changed,
            dfs,
            discord_player,
            ids,
            channel,
            # patch,
            player_discord_id,
            # dates_this_event,
            league_roles_all,
            position_roles,
            # roles,
            skipped,
            # member_lookup,
            unchanged,
            # debug_channel,
        )

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


async def get_position_roles(roles):
    return {role_id_to_position[role.id]: role for role in roles if role.id in role_id_to_position}
    # filtered_roles = [role for role in roles if await role_only_champ_tourney_roles_check(role)]
    # return dict(sorted([(int(role.name.split()[-1]), role) for role in filtered_roles]))


async def get_league_roles(roles, league):
    if league == champ:
        initial = [(int(role.name.split()[-1]), role) for role in roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))]
        only_250 = [item for item in initial if item[0] == 250]  # remove me when others disappear
        return dict(sorted(only_250, reverse=True))

    return dict(
        sorted(
            [(500, role) for role in roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))],
            reverse=True,
        ),
    )


async def handle_champ_position_roles(
    df,
    position_roles,
    discord_player,
    changed,
    unchanged,
    # dates_this_event,
) -> bool:
    # position_roles = await get_position_roles(roles)
    logging.debug(f"{discord_player=} {df.position=}")

    if df.sort_values("date", ascending=False).iloc[0].position == 1:  # special logic for the winner
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

    # current_df = df[df["date"].isin(dates_this_event)]
    current_df = df
    best_position_in_event = current_df.position.min() if not current_df.empty else 100000

    for pos, role in sorted(tuple(position_roles.items()))[1:]:
        if best_position_in_event <= pos:
            rightful_role = role

            if rightful_role in discord_player.roles:
                unchanged[champ].append((discord_player, rightful_role))
                return True  # Don't actually do anything if the player already has the role

            for role in [role for role in discord_player.roles if role.id in role_id_to_position]:
                await discord_player.remove_roles(role)

            await discord_player.add_roles(rightful_role)
            logging.info(f"Added {role=} to {discord_player=}")
            changed[champ].append((discord_player.name, rightful_role.name))
            return True
    else:
        for role in [role for role in discord_player.roles if role.id in role_id_to_position]:
            await discord_player.remove_roles(role)

    return False


async def handle_leagues(
    all_leagues,
    changed,
    dfs,
    discord_player,
    ids,
    channel,
    # patch,
    player_discord_id,
    # dates_this_event,
    # roles,
    league_roles_all,
    position_roles,
    skipped,
    # member_lookup,
    unchanged,
    # debug_channel,
):
    for league in all_leagues:
        # league_roles = await get_league_roles(roles, league)
        league_roles = league_roles_all[league]
        df = dfs[league]

        # player_df = df[df["real_name"] == player.name]
        player_df = df[df["id"].isin(ids)]

        if player_df.empty:
            continue

        if discord_player is None:
            return None, skipped + 1

        if league == champ:
            await handle_champ_position_roles(
                player_df,
                position_roles,
                discord_player,
                changed,
                unchanged,
                # dates_this_event,
            )
            return discord_player, skipped  # don't give out wave role for champ

        gets_500 = any(wave >= 500 for wave in player_df.wave)

        if league_roles and gets_500:
            rightful_role = league_roles[500]
            wave_bottom = 500
        else:
            continue

        current_champ_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, get_safe_league_prefix(league))]
        current_champ_waves = [500 for role in current_champ_roles]

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
