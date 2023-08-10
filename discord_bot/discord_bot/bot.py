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
from discord_bot.purge_roles import purge_all_tourney_roles
from discord_bot.remove_nicknames import remove_nicknames
from discord_bot.util import (
    get_tower,
    get_verified_role,
    handle_outside,
    id_098799,
    is_player_id_please_room,
    is_testing_room,
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
        channel = await client.fetch_channel(930105733998080062)

        # those are the top level functionalities one may want to test
        # await handle_adding(client, limit=5, channel=channel, verbose=True)
        # await remove_nicknames(client, channel)
        # await purge_all_tourney_roles(
        #     client=client,
        #     channel=channel,
        #     players=await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False, discord_id=id_098799),
        # )
        # await handle_role_present(client, await (await get_tower(client)).fetch_member(id_098799))
        exit()
    logging.info(f"We have logged in as {client.user}")

    if not handle_roles_scheduled.is_running():
        handle_roles_scheduled.start()


@client.event
async def on_message(message):
    try:
        if is_testing_room(message.channel) and message.content.startswith("!remove_all_nicknames"):
            await remove_nicknames(client, message.channel)

        elif is_testing_room(message.channel) and message.content.startswith("!add_roles"):
            try:
                limit = int(message.content.split()[1])
            except Exception:
                limit = None

            await handle_adding(client, limit, message.channel, verbose=True)

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
    tower = await get_tower(client)
    channel = client.get_channel(role_log_room_id)
    test_channel = await tower.fetch_channel(testing_room_id)

    try:
        await handle_adding(client, limit=None, channel=channel, debug_channel=test_channel, verbose=False)
    except Exception as e:
        await test_channel.send(f"😱😱😱 \n\n {e}")
        logging.exception(e)


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
