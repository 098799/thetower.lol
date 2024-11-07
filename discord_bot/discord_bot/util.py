import os
from discord_bot import const
from functools import partial

from asyncstdlib.functools import lru_cache

handle_outside = bool(os.getenv("GO"))


@lru_cache
async def get_tower(client):
    """We only want to fetch the server once."""
    return await client.fetch_guild(const.guild_id)


@lru_cache
async def get_verified_role(client):
    """We only want to fetch the verified role."""
    return (await get_tower(client)).get_role(const.verified_role_id)


def is_channel(channel, id_):
    return channel.id == id_


is_t50_channel = partial(is_channel, id_=const.top50_channel_id)
is_meme_channel = partial(is_channel, id_=const.meme_channel_id)
is_testing_channel = partial(is_channel, id_=const.testing_channel_id)
is_helpers_channel = partial(is_channel, id_=const.helpers_channel_id)
is_player_id_please_channel = partial(is_channel, id_=const.verify_channel_id)
is_role_count_channel = partial(is_channel, id_=const.role_count_channel_id)


def is_098799(author):
    return author.id == const.id_098799


def is_andreas(author):
    return author.id == const.id_andreas


def is_fishy(author):
    return author.id == const.id_fishy  # super tiny author 😂


def get_safe_league_prefix(league):
    return league[:-1]


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and "500" in role.name.strip()


position_role_ids = {
    1: const.top1_id,
    10: const.top10_id,
    25: const.top25_id,
    50: const.top50_id,
    100: const.top100_id,
    200: const.top200_id,
    300: const.top300_id,
    400: const.top400_id,
    500: const.top500_id,
    # 600: const.top600_id,
    750: const.top750_id,
    # 800: const.top800_id,
    # 900: const.top900_id,
    1000: const.top1000_id,
    1500: const.top1500_id,
    # 2000: const.top2000_id,
}


role_id_to_position = {value: key for key, value in position_role_ids.items()}


async def role_only_champ_tourney_roles_check(role):
    return role in position_role_ids.values()


async def get_all_members(client):
    guild = await get_tower(client)

    members = []

    async for member in guild.fetch_members():
        members.append(member)

    return members
