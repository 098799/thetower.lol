import logging
import os
from collections import defaultdict

import discord
import django
from asgiref.sync import sync_to_async
from asyncstdlib.functools import lru_cache
from discord.ext import tasks
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

verified_role_id = 1119950199209611274
testing_room_id = 930105733998080062


async def get_member(guild, discord_id, channel=None):
    try:
        return await guild.fetch_member(discord_id)
    except discord.errors.NotFound:
        logging.info(f"Failed to fetch {discord_id=}")

        if channel:
            await channel.send(f"😱😱😱 Failed to fetch data for discord_id {discord_id}, please review.")


async def handle_adding(limit, channel=None):
    skipped = 0
    unchanged = defaultdict(list)
    changed = defaultdict(list)

    players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)

    await channel.send(f"Starting the processing of {players.count() if not limit else limit} users... :rocket:")

    all_leagues = leagues

    dfs = {league: load_tourney_results__uncached(league_to_folder[league]) for league in all_leagues}

    patch = await sync_to_async(Patch.objects.get, thread_sensitive=True)(version_minor=19, beta=False)
    tower = await get_tower()
    roles = await tower.fetch_roles()

    player_iter = players.order_by("-id")[:limit] if limit else players.order_by("-id")

    for player in tqdm(player_iter):
        ids = await sync_to_async(player.ids.all().values_list, thread_sensitive=True)("id", flat=True)
        discord_player = None

        discord_player, skipped = await handle_leagues(all_leagues, changed, dfs, discord_player, ids, channel, patch, player, roles, skipped, tower, unchanged)

        if discord_player is None:
            discord_player = await get_member(tower, int(player.discord_id), channel=channel)

            if discord_player is None:
                continue

        elif discord_player == "unknown":
            break

    logging.info(f"{skipped=}")

    await channel.send(f"Successfully reviewed all players :tada: \n\n{skipped=} (no role eligible), \n{len(unchanged)=}, \n{changed=}.")
    logging.info("**********Done**********")


async def handle_leagues(all_leagues, changed, dfs, discord_player, ids, channel, patch, player, roles, skipped, tower, unchanged):
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
        discord_player = await get_member(tower, int(player.discord_id), channel=channel)

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
        changed[league].append((discord_player, rightful_role))
        logging.info(f"Added {rightful_role=} to {discord_player=}")

    else:
        unchanged[league].append((discord_player, rightful_role))


async def handle_role_present(discord_player):
    verified_role = await get_verified_role()

    has_player_id_present_role = [role for role in discord_player.roles if role.id == verified_role_id]

    if not has_player_id_present_role:
        await discord_player.add_roles(verified_role)


async def remove_nicknames(channel=None):
    tower = await get_tower()
    channel = channel if channel else client.fetch_channel(testing_room_id)

    success = 0
    failure = 0

    await channel.send("Starting to remove nicknames from people...")

    # for member in [await tower.fetch_member(177504210177228801)]:  # uncomment me to test
    async for member in tower.fetch_members():
        try:
            await member.edit(nick=None)
            success += 1
        except Exception:
            await channel.send(f"😱😱😱 Failed to remove nickname from {member}, continuing...")
            failure += 1

        if (success + failure) % 500 == 0:
            await channel.send(f"Removed {success=} {failure=}")

        if (success + failure) % 10 == 0:
            logging.info(f"{success=} {failure=}")

    await channel.send(f"Finished removing nicknames from people, {success=}, {failure=}")


def is_testing_room(channel):
    return channel.id == testing_room_id


def is_player_id_please_room(channel):
    return channel.id == 1117867265375879259


def is_098799(author):
    return author.id == 177504210177228801


def is_andreas(author):
    return author.id == 181859318801498113


@client.event
async def on_ready():
    if handle_outside:
        # for local testing, this channel is private discord so we don't pollute tower discord
        # it doesn't guarantee that you won't create side-effects, so careful
        channel = client.get_channel(1117480385941618800)

        # those are the top level functionalities one may want to test
        # await handle_adding(limit=5, channel=channel)
        # await remove_nicknames(channel)
        # await purge_all_tourney_roles(channel=channel, players=await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False, discord_id=177504210177228801))
        await handle_role_present(await (await get_tower()).fetch_member(177504210177228801))
        exit()
    logging.info(f"We have logged in as {client.user}")

    if not handle_roles_scheduled.is_running():
        handle_roles_scheduled.start()


@lru_cache
async def get_tower():
    """We only want to fetch the server once."""
    return await client.fetch_guild(850137217828388904)


@lru_cache
async def get_verified_role():
    """We only want to fetch the verified role."""
    return (await get_tower()).get_role(verified_role_id)


@client.event
async def on_message(message):
    try:
        if is_testing_room(message.channel) and message.content.startswith("!remove_all_nicknames"):
            await remove_nicknames(message.channel)

        elif is_testing_room(message.channel) and message.content.startswith("!add_roles"):
            try:
                limit = int(message.content.split()[1])
            except Exception:
                limit = None

            await handle_adding(limit, message)

        elif is_player_id_please_room(message.channel) and message.author.id != 1117480944153145364:
            await validate_player_id(message)

        # elif is_testing_room(message.channel) and message.author.id != 1117480944153145364 and is_098799(message.author):
        #     await validate_player_id(message)

        elif is_testing_room(message.channel) and message.content.startswith("!purge_all_tourney_roles"):
            players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(
                approved=True, discord_id__isnull=False, discord_id=177504210177228801
            )
            await purge_all_tourney_roles(message.channel, players)
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
            discord_player = await (await get_tower()).fetch_member(player.discord_id)
            await handle_role_present(discord_player)
            await message.add_reaction("✅")
        else:
            await message.add_reaction("⁉️")
    except Exception as exc:
        await message.channel.send(f"Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def purge_all_tourney_roles(channel, players):
    purged = 0
    try:
        tower = await get_tower()
        discord_players = []

        for player in players:
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
            for discord_player in discord_players:
                current_league_roles = [role for role in discord_player.roles if await role_prefix_and_only_tourney_roles_check(role, safe_league_prefix)]

                if len(current_league_roles) > 0:
                    await discord_player.remove_roles(*current_league_roles)
                    purged += 1
                else:
                    logging.info(f"name: {discord_player.name} roles that should have been removed: {current_league_roles}")

        await channel.send(f"🔥🔥🔥 Purged {purged} tournament roles 🔥🔥🔥")

    except Exception as exc:
        await channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and role.name.strip().endswith("0")


def get_safe_league_prefix(league):
    return league[:-1]


@tasks.loop(hours=1.0)
async def handle_roles_scheduled():
    tower = await get_tower()
    channel = await tower.fetch_channel(testing_room_id)

    try:
        await handle_adding(limit=None, channel=channel)
    except Exception as e:
        logging.exception(e)


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
