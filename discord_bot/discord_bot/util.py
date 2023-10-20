import os
import re
from functools import partial

from asyncstdlib.functools import lru_cache

from dtower.tourney_results.constants import top

handle_outside = bool(os.getenv("GO"))

verified_role_id = 1119950199209611274
testing_room_id = 930105733998080062
helpers_room_id = 1006900314588336139
role_log_room_id = 1128308502130081842
id_098799 = 177504210177228801
meme_channel_id = 1159121488931209328
role_count_channel_id = 1164883276243140638


@lru_cache
async def get_tower(client):
    """We only want to fetch the server once."""
    return await client.fetch_guild(850137217828388904)


@lru_cache
async def get_verified_role(client):
    """We only want to fetch the verified role."""
    return (await get_tower(client)).get_role(verified_role_id)


def is_channel(channel, id_):
    return channel.id == id_


is_meme_room = partial(is_channel, id_=meme_channel_id)
is_testing_room = partial(is_channel, id_=testing_room_id)
is_helpers_room = partial(is_channel, id_=helpers_room_id)
is_player_id_please_room = partial(is_channel, id_=1117867265375879259)
is_role_count_room = partial(is_channel, id_=role_count_channel_id)


def is_098799(author):
    return author.id == id_098799


def is_andreas(author):
    return author.id == 181859318801498113


def get_safe_league_prefix(league):
    return league[:-1]


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and role.name.strip().endswith("0")


async def role_only_champ_tourney_roles_check(role):
    return re.findall(rf"{top}\s\d", role.name.strip())
