import logging

from tqdm import tqdm

from discord_bot.util import get_safe_league_prefix, get_tower, role_prefix_and_only_tourney_roles_check, role_only_legend_tourney_roles_check
from dtower.tourney_results.constants import leagues


async def purge_all_tourney_roles(client, channel, players):
    purged = 0
    try:
        await channel.send("Starting carnage...")
        tower = await get_tower(client)
        discord_players = []

        for player in tqdm(players):
            try:
                current_player = await tower.fetch_member(int(player.discord_id))
                discord_players.append(current_player)
            except Exception as exc:
                logging.info(f"Player {player.name} could not be found. \n\n {exc}")
                continue

        logging.info(f"Retrieved {len(discord_players)} players")
        await channel.send(f"Found {len(discord_players)} players")

        for league in leagues:
            safe_league_prefix = get_safe_league_prefix(league)
            for discord_player in tqdm(discord_players):
                current_league_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, safe_league_prefix)]
                if league.startswith("Legend"):
                    current_league_roles.append([role for role in discord_player.roles if await role_only_legend_tourney_roles_check(role)])

                purged = await purge_current_league_roles(current_league_roles, discord_player, purged)

        await channel.send(f"🔥🔥🔥 Purged {purged} tournament roles 🔥🔥🔥")

    except Exception as exc:
        await channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def purge_current_league_roles(current_league_roles, discord_player, purged):
    if len(current_league_roles) > 0:
        await discord_player.remove_roles(*current_league_roles)
        purged += 1
    else:
        logging.info(f"name: {discord_player.name} roles that should have been removed: {current_league_roles}")
    return purged
