import logging
import os
from collections import defaultdict

import discord
import django
from asgiref.sync import sync_to_async
from tqdm import tqdm

from dtower.tourney_results.constants import league_to_folder, leagues
from dtower.tourney_results.data import load_tourney_results__uncached

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from dtower.sus.models import KnownPlayer, PlayerId
from dtower.tourney_results.models import PatchNew as Patch

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)


handle_outside = bool(os.getenv("GO"))


async def get_member(guild, discord_id, message=None):
    try:
        return await guild.fetch_member(discord_id)
    except discord.errors.NotFound:
        logging.info(f"Failed to fetch {discord_id=}")

        if message:
            await message.channel.send(f"😱😱😱 Failed to fetch data for discord_id {discord_id}, please review.")


async def handle_adding(limit, message=None, verbose=False):
    skipped = 0
    unchanged = defaultdict(int)
    changed = defaultdict(int)

    players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)

    if verbose:
        await message.channel.send(f"Starting the processing of {players.count() if not limit else limit} users... :rocket:")

    all_leagues = leagues

    dfs = {league: load_tourney_results__uncached(league_to_folder[league]) for league in all_leagues}

    patch = await sync_to_async(Patch.objects.get, thread_sensitive=True)(version_minor=19, beta=False)
    tower = await client.fetch_guild(850137217828388904)
    roles = await tower.fetch_roles()

    player_iter = players.order_by("-id")[:limit] if limit else players.order_by("-id")

    player_id_present_role_id = 1119950199209611274
    player_id_present_role = [role for role in roles if role.id == player_id_present_role_id][0]

    added_role = 0
    had_role = 0

    for player in tqdm(player_iter):
        ids = await sync_to_async(player.ids.all().values_list, thread_sensitive=True)("id", flat=True)
        discord_player = None

        discord_player, skipped = await handle_leagues(
            all_leagues, changed, dfs, discord_player, ids, message, patch, player, roles, skipped, tower, unchanged, verbose
        )

        if discord_player is None:
            discord_player = await get_member(tower, int(player.discord_id), message=message)

            if discord_player is None:
                continue

        elif discord_player == "unknown":
            break

        added_role, had_role = await handle_role_present(added_role, discord_player, had_role, player_id_present_role, player_id_present_role_id)

    logging.info(f"{skipped=}")

    if verbose:
        await message.channel.send(f"Successfully reviewed all players :tada: \n\n{skipped=} (no role eligible), \n{unchanged=}, \n{changed=}.")
        await message.channel.send(f"special Pog role: {had_role=}, {added_role=}")
    logging.info("**********Done**********")


async def handle_leagues(all_leagues, changed, dfs, discord_player, ids, message, patch, player, roles, skipped, tower, unchanged, verbose):
    for league in all_leagues:
        safe_league_prefix = get_safe_league_prefix(league)
        league_roles = dict(
            sorted(
                [(int(role.name.split()[-1]), role) for role in roles if role.name.strip().startswith(safe_league_prefix) and role.name.strip().endswith("0")],
                reverse=True,
            )
        )
        df = dfs[league]

        player_df = df[df["real_name"] == player.name]
        player_df = player_df[player_df["id"].isin(ids)]
        patch_df = player_df[player_df["patch"] == patch]

        if patch_df.empty:
            continue

        wave_bottom = patch_df.iloc[-1].name_role.wave_bottom

        if wave_bottom == 0:
            continue

        rightful_role = league_roles[wave_bottom]
        # this should be extracted into a method
        discord_player = await get_member(tower, int(player.discord_id), message=message)

        if discord_player is None:
            return None, skipped + 1

        current_champ_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, safe_league_prefix)]
        current_champ_waves = [int(role.name.strip().split()[-1]) for role in current_champ_roles]

        await iterate_waves_and_add_roles(changed, current_champ_roles, current_champ_waves, discord_player, league, rightful_role, unchanged, wave_bottom)

        break

    else:
        skipped += 1
    return discord_player, skipped


async def iterate_waves_and_add_roles(changed, current_champ_roles, current_champ_waves, discord_player, league, rightful_role, unchanged, wave_bottom):
    if all(wave_bottom > wave for wave in current_champ_waves):
        for champ_role in current_champ_roles:
            await discord_player.remove_roles(champ_role)

        await discord_player.add_roles(rightful_role)
        changed[league] += 1
        logging.info(f"Added {rightful_role=} to {discord_player=}")

    else:
        unchanged[league] += 1


async def handle_role_present(added_role, discord_player, had_role, player_id_present_role, player_id_present_role_id):
    has_player_id_present_role = [role for role in discord_player.roles if role.id == player_id_present_role_id]
    if not has_player_id_present_role:
        await discord_player.add_roles(player_id_present_role)
        added_role += 1
    else:
        had_role += 1
    return added_role, had_role


@client.event
async def on_ready():
    if handle_outside:
        await handle_adding(limit=None, message=None, verbose=False)
        exit()
    logging.info(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    try:
        if message.channel.id == 930105733998080062 and message.content.startswith("!add_roles"):
            try:
                limit = int(message.content.split()[1])
            except Exception:
                limit = None

            await handle_adding(limit, message, verbose=True)

        # elif message.channel.id == 930105733998080062 and message.author.id != 1117480944153145364:
        elif message.channel.id == 1117867265375879259 and message.author.id != 1117480944153145364:
            await validate_player_id(message)

        elif message.channel.id == 930105733998080062 and message.content.startswith("!remove_all_roles"):
            tower = await client.fetch_guild(850137217828388904)
            players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)
            roles = await tower.fetch_roles()
            champ_roles = dict(sorted([(int(role.name.split()[-1]), role) for role in roles if role.name.strip().startswith("Champ")], reverse=True))

            for player in players:
                logging.info(f"Checking {player=}")
                discord_player = await tower.fetch_member(int(player.discord_id))

                current_champ_roles = [role for role in discord_player.roles if role.name.startswith("Champ")]

                for champ_role in current_champ_roles:
                    await discord_player.remove_roles(champ_role)

                await discord_player.add_roles(champ_roles[500])
                logging.info(f"Removed roles for {player=}")
        elif message.channel.id == 930105733998080062 and message.content.startswith("!purge_all_tourney_roles"):
            await purge_all_tourney_roles(message)
            logging.info("Purged all tournaments roles")

    except Exception as exc:
        await message.channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def validate_player_id(message):
    try:
        if 17 > len(message.content) > 12 and message.attachments:
            player, created = await sync_to_async(KnownPlayer.objects.get_or_create, thread_sensitive=True)(
                discord_id=message.author.id, defaults=dict(approved=True, name=message.author.name)
            )
            await sync_to_async(PlayerId.objects.update_or_create, thread_sensitive=True)(id=message.content, player_id=player.id, defaults=dict(primary=True))
            await message.add_reaction("✅")
        else:
            await message.add_reaction("⁉️")
    except Exception as exc:
        await message.channel.send(f"Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def purge_all_tourney_roles(message):
    purged = 0
    try:
        tower = await client.fetch_guild(850137217828388904)
        players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)
        discord_players = []

        for player in players:
            try:
                current_player = await tower.fetch_member(int(player.discord_id))
                discord_players.append(current_player)
            except Exception as exc:
                logging.info(f"Player {player.name} could not be found. \n\n {exc}")
                continue

        logging.info(f"Retrieved {len(discord_players)} players")
        await message.channel.send(f"Found {len(discord_players)} players")

        for league in leagues:
            safe_league_prefix = await get_safe_league_prefix(league)
            for discord_player in discord_players:
                current_league_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, safe_league_prefix)]

                if len(current_league_roles) > 0:
                    await discord_player.remove_roles(*current_league_roles)
                    purged += 1
                else:
                    logging.info(f"name: {discord_player.name} roles that should have been removed: {current_league_roles}")

        await message.channel.send(f"🔥🔥🔥 Purged {purged} tournament roles 🔥🔥🔥")

    except Exception as exc:
        await message.channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and role.name.strip().endswith("0")


async def get_safe_league_prefix(league):
    safe_league_prefix = league[:-1]
    return safe_league_prefix


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
