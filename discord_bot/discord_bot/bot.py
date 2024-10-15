import asyncio
import logging
import os

import discord
import django
from discord_bot import const
from discord.ext import tasks

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from discord_bot.add_roles import handle_adding
from discord_bot.remove_nicknames import remove_nicknames
from discord_bot.util import get_tower, handle_outside, is_testing_channel

semaphore = asyncio.Semaphore(1)

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    if handle_outside:
        # for local testing, this channel is private discord so we don't pollute tower discord
        # it doesn't guarantee that you won't create side-effects, so careful
        channel = client.get_channel(const.testing_channel_id)
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


@client.event
async def on_message(message):
    try:
        if is_testing_channel(message.channel) and message.content.startswith("!remove_all_nicknames"):
            await remove_nicknames(client, message.channel)

        # elif is_meme_channel(message.channel) and message.content.startswith("!rename"):
        #     if "Top 1" in {role.name for role in message.author.roles}:
        #         new_name = message.content.split(" ", 1)[1]

        #         channel = await client.fetch_channel(meme_channel_id)
        #         await channel.edit(name=new_name)
        #         await message.channel.send(f"🔥 Renamed channel to {new_name} 🔥")

        # elif is_testing_channel(message.channel) and message.content.startswith("!check_id"):
        #     try:
        #         await check_id(client, message)
        #     except Exception as exc:
        #         logging.exception(exc)

        elif is_testing_channel(message.channel) and message.content.startswith("!add_roles"):
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

            async with semaphore:
                await handle_adding(
                    client,
                    limit=limit,
                    discord_ids=discord_ids,
                    channel=message.channel,
                    debug_channel=message.channel,
                    verbose=True,
                )

        # elif is_testing_channel(message.channel) and message.content.startswith("!purge_all_tourney_roles"):
        #     players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(approved=True, discord_id__isnull=False)
        #     await purge_all_tourney_roles(client, message.channel, players)
        #     logging.info("Purged all tournaments roles")

    except Exception as exc:
        await message.channel.send(f"😱😱😱 Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


@tasks.loop(hours=1.0)
async def handle_roles_scheduled():
    async with semaphore:
        try:
            tower = await get_tower(client)
            channel = await client.fetch_channel(const.role_log_channel_id)
            test_channel = await tower.fetch_channel(const.testing_channel_id)

            try:
                await handle_adding(client, limit=None, channel=channel, debug_channel=test_channel, verbose=False)
            except Exception as e:
                await test_channel.send(f"😱😱😱 \n\n {e}")
                logging.exception(e)
        except Exception as e:
            print("Top level exception")
            logging.exception(e)


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
