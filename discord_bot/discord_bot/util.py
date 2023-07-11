import os

from asyncstdlib.functools import lru_cache

handle_outside = bool(os.getenv("GO"))

verified_role_id = 1119950199209611274
testing_room_id = 930105733998080062
role_log_room_id = 1128308502130081842
id_098799 = 177504210177228801


@lru_cache
async def get_tower(client):
    """We only want to fetch the server once."""
    return await client.fetch_guild(850137217828388904)


@lru_cache
async def get_verified_role(client):
    """We only want to fetch the verified role."""
    return (await get_tower(client)).get_role(verified_role_id)


def is_testing_room(channel):
    return channel.id == testing_room_id


def is_player_id_please_room(channel):
    return channel.id == 1117867265375879259


def is_098799(author):
    return author.id == id_098799


def is_andreas(author):
    return author.id == 181859318801498113


def get_safe_league_prefix(league):
    return league[:-1]


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and role.name.strip().endswith("0")
