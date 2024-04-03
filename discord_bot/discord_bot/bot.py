import logging
import os

import discord
import django
from asgiref.sync import sync_to_async
from discord.ext import tasks

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from discord_bot.add_roles import handle_adding
from discord_bot.print_role_counts import print_roles
from discord_bot.purge_roles import purge_all_tourney_roles
from discord_bot.remove_nicknames import remove_nicknames
from discord_bot.util import (
    get_tower,
    get_verified_role,
    handle_outside,
    id_098799,
    is_meme_room,
    is_player_id_please_room,
    is_role_count_room,
    is_testing_room,
    meme_channel_id,
    role_log_room_id,
    testing_room_id,
    verified_role_id,
)
from discord_bot.validate_id import handle_role_present, validate_player_id
from dtower.sus.models import KnownPlayer, PlayerId

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)


@client.event
async def on_ready():
    if handle_outside:
        # for local testing, this channel is private discord so we don't pollute tower discord
        # it doesn't guarantee that you won't create side-effects, so careful
        channel = client.get_channel(testing_room_id)
        await handle_adding(
            client,
            limit=100,
            discord_ids=None,
            channel=channel,
            verbose=False,
        )

        exit()
    logging.info(f"We have logged in as {client.user}")

    # await handle_adding(
    #     client,
    #     limit=5,
    #     discord_ids=[249001511957299200],
    #     channel=None,
    #     debug_channel=None,
    #     verbose=False,
    # )
    if not handle_roles_scheduled.is_running():
        handle_roles_scheduled.start()


async def check_id(client, message):
    _, *potential_ids = message.content.split()

    for potential_id in potential_ids:
        players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id=potential_id)

        if players:
            player = await sync_to_async(players.get)()

            ids = player.ids.all().values("id", "primary")
            await message.channel.send(f"{player.discord_id=}, {ids=}")

        player_ids = await sync_to_async(PlayerId.objects.filter, thread_sensitive=True)(id=potential_id)

        if player_ids:
            for player_id in player_ids:
                await message.channel.send(f"{player_id.player.discord_id=}, {player_id.id=}, {player_id.primary=}")


@client.event
async def on_message(message):
    try:
        if is_testing_room(message.channel) and message.content.startswith("!remove_all_nicknames"):
            await remove_nicknames(client, message.channel)

        elif (is_testing_room(message.channel) or is_role_count_room(message.channel)) and message.content.startswith("!role_counts"):
            await print_roles(client, message)

        elif is_meme_room(message.channel) and message.content.startswith("!rename"):
            if "Top 1" in {role.name for role in message.author.roles}:
                new_name = message.content.split(" ", 1)[1]

                channel = await client.fetch_channel(meme_channel_id)
                await channel.edit(name=new_name)
                await message.channel.send(f"🔥 Renamed channel to {new_name} 🔥")

        elif is_testing_room(message.channel) and message.content.startswith("!check_id"):
            try:
                await check_id(client, message)
            except Exception as exc:
                logging.exception(exc)

        elif is_testing_room(message.channel) and message.content.startswith("!add_roles"):
            try:
                command, argument = message.content.split()

                if len(argument) < 10:
                    discord_ids = None
                    limit = int(argument)
                else:
                    discord_ids = [int(argument)]
                    limit = None
            except Exception:
                limit = None
                discord_ids = None

            await handle_adding(
                client,
                limit=limit,
                discord_ids=discord_ids,
                channel=message.channel,
                debug_channel=message.channel,
                verbose=True,
            )

        elif is_player_id_please_room(message.channel) and message.author.id != 1117480944153145364:
            await validate_player_id(client, message)

        # elif is_testing_room(message.channel) and message.author.id != 1117480944153145364 and is_098799(message.author):
        #     await validate_player_id(client, message)

        elif is_testing_room(message.channel) and message.content.startswith("!purge_all_tourney_roles"):
            players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)
            await purge_all_tourney_roles(client, message.channel, players)
            logging.info("Purged all tournaments roles")

    except Exception as exc:
        await message.channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


@tasks.loop(hours=1.0)
async def handle_roles_scheduled():
    try:
        tower = await get_tower(client)
        channel = client.get_channel(role_log_room_id)
        test_channel = await tower.fetch_channel(testing_room_id)

        try:
            await handle_adding(client, limit=None, channel=channel, debug_channel=test_channel, verbose=False)
        except Exception as e:
            await test_channel.send(f"😱😱😱 \n\n {e}")
            logging.exception(e)
    except Exception as e:
        print("Top level exception")
        logging.exception(e)


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
