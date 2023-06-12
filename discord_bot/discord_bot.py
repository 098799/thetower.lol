import asyncio
import logging
import os

import discord
import django
from asgiref.sync import sync_to_async

from dtower.tourney_results.constants import champ, league_to_folder
from dtower.tourney_results.data import load_tourney_results

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtower.thetower.settings")
django.setup()

from dtower.sus.models import KnownPlayer
from dtower.tourney_results.models import PatchNew as Patch

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.channel.id == 930105733998080062 and message.content.startswith("!add_roles"):
        league = champ
        df = load_tourney_results(league_to_folder[league])

        players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(discord_id__isnull=False)
        patch = await sync_to_async(Patch.objects.get, thread_sensitive=True)(version_minor=19, beta=False)
        tower = await client.fetch_guild(850137217828388904)
        roles = await tower.fetch_roles()
        champ_roles = dict(sorted([(int(role.name.split()[-1]), role) for role in roles if role.name.strip().startswith("Champ")], reverse=True))

        for player in players:
            logger.info(f"Checking {player=}")
            discord_player = await tower.fetch_member(int(player.discord_id))
            player_df = df[df["real_name"] == player.name]
            patch_df = player_df[player_df["patch"] == patch]

            if patch_df.empty:
                continue

            wave_bottom = patch_df.iloc[-1].name_role.wave_bottom

            rightful_role = champ_roles[wave_bottom]

            current_champ_roles = [role for role in discord_player.roles if role.name.startswith("Champ")]
            current_champ_waves = [int(role.name.strip().split()[-1]) for role in current_champ_roles]

            if all(wave_bottom > wave for wave in current_champ_waves):
                for champ_role in current_champ_roles:
                    await discord_player.remove_roles(champ_role)

                await discord_player.add_roles(rightful_role)
                logger.info(f"Added {rightful_role=} to {discord_player=}")

    if message.channel.id == 930105733998080062 and message.content.startswith("!remove_all_roles"):
        tower = await client.fetch_guild(850137217828388904)
        players = await sync_to_async(KnownPlayer.objects.filter, thread_sensitive=True)(discord_id__isnull=False)
        roles = await tower.fetch_roles()
        champ_roles = dict(sorted([(int(role.name.split()[-1]), role) for role in roles if role.name.strip().startswith("Champ")], reverse=True))

        for player in players:
            logger.info(f"Checking {player=}")
            discord_player = await tower.fetch_member(int(player.discord_id))

            current_champ_roles = [role for role in discord_player.roles if role.name.startswith("Champ")]

            for champ_role in current_champ_roles:
                await discord_player.remove_roles(champ_role)

            await discord_player.add_roles(champ_roles[500])
            logger.info(f"Removed roles for {player=}")

    if message.channel.id == 930105733998080062 and message.content.startswith("!remove_role"):
        discord_player = message.author

        tower = await client.fetch_guild(850137217828388904)
        current_champ_roles = [role for role in discord_player.roles if role.name.startswith("Champ")]

        for champ_role in current_champ_roles:
            await discord_player.remove_roles(champ_role)

    # if message.channel.id == 930105733998080062 and message.content.startswith("!remove_roles"):
    #     tower = await client.fetch_guild(850137217828388904)
    #     breakpoint()
    #     discord_player = await tower.fetch_member(message)
    # elif message.channel.id == 930105733998080062 and message.content.startswith("!add_roles"):
    #     tower = await client.fetch_guild(850137217828388904)

    #     roles = await tower.fetch_roles()

    #     champ_roles = [role for role in roles if role.name.strip().startswith("Champ")]
    #     breakpoint()
    #     ...

    # if message.author.id == 177504210177228801 and message.content.startswith("!remove_roles"):
    #     guild = await client.fetch_guild(1117480385010466886)

    #     for role in guild.roles:
    #         if role.name == "foo":
    #             async for member in guild.fetch_members():
    #                 if role in member.roles:
    #                     await member.remove_roles(role)
    #                     logger.info(f"Removed {role=} to {member=}")

    # elif message.author.id == 177504210177228801 and message.content.startswith("!add_roles"):
    #     guild = await client.fetch_guild(1117480385010466886)

    #     for role in guild.roles:
    #         if role.name == "foo":
    #             async for member in guild.fetch_members():
    #                 if role not in member.roles:
    #                     await member.add_roles(role)
    #                     logger.info(f"Added {role=} to {member=}")


# @client.event
# async def on_message(message):
#     breakpoint()
#     if message.author.id == 177504210177228801 and message.content.startswith("!remove_roles"):
#         guild = await client.fetch_guild(1117480385010466886)

#         for role in guild.roles:
#             if role.name == "foo":
#                 async for member in guild.fetch_members():
#                     if role in member.roles:
#                         await member.remove_roles(role)
#                         logger.info(f"Removed {role=} to {member=}")

#     elif message.author.id == 177504210177228801 and message.content.startswith("!add_roles"):
#         guild = await client.fetch_guild(1117480385010466886)

#         for role in guild.roles:
#             if role.name == "foo":
#                 async for member in guild.fetch_members():
#                     if role not in member.roles:
#                         await member.add_roles(role)
#                         logger.info(f"Added {role=} to {member=}")


client.run(os.getenv("DISCORD_TOKEN"), log_level=logging.INFO)
