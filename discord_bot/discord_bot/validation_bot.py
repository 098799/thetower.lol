import logging
import os

import discord
import django

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from asgiref.sync import sync_to_async

from discord_bot.print_role_counts import print_roles
from discord_bot.util import is_player_id_please_room, is_role_count_room, is_t50_room, is_testing_room, t50_channel_id, top1_id
from discord_bot.validate_id import validate_player_id
from dtower.sus.models import KnownPlayer, PlayerId
from dtower.tourney_results.models import Injection

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)


@client.event
async def on_ready():
    pass


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
        if is_player_id_please_room(message.channel) and message.author.id != 1117480944153145364:
            logging.info(message.channel)
            print(message.channel)
            await validate_player_id(client, message)
        elif is_testing_room(message.channel) and message.content.startswith("!check_id"):
            try:
                await check_id(client, message)
            except Exception as exc:
                logging.exception(exc)
        elif (is_testing_room(message.channel) or is_role_count_room(message.channel)) and message.content.startswith("!role_counts"):
            await print_roles(client, message)
        elif is_t50_room(message.channel) and message.content.startswith("!inject"):
            if top1_id in {role.id for role in message.author.roles}:
                injection = message.content.split(" ", 1)[1]
                Injection.objects.create(text=injection, user=message.author.id)
                await message.channel.send(f"🔥 Stored the prompt injection for AI summary: {injection[:10]}... 🔥")
    except Exception as exc:
        await message.channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)