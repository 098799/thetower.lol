import os
from functools import partial

from asyncstdlib.functools import lru_cache

handle_outside = bool(os.getenv("GO"))

#user ids
id_098799 = 177504210177228801
id_andreas = 181859318801498113
id_fishy = 169201175231463424

#room ids
helpers_room_id = 1006900314588336139
meme_room_id = 1159121488931209328
role_count_room_id = 1164883276243140638
role_log_room_id = 1128308502130081842
t50_room_id = 903354378403065949
testing_room_id = 930105733998080062

#role ids
verified_role_id = 1119950199209611274

##champ ids
top1_id = 993947001232298126
top10_id = 1111025773856440410
top25_id = 1126993498294468709
top50_id = 1126993501238857749
top100_id = 1126993504330063934
top200_id = 1148207928407490570
top300_id = 1148207929665794068
top400_id = 1148207931024740412
top500_id = 1148207932173987870
top600_id = 1111011421141086289
top700_id = 1111011432738344960
top800_id = 1077324438657306744
top900_id = 1077324395598594150
top1000_id = 993946810240483347
top1500_id = 993946632120975512
top2000_id = 993946090061713571

##other league ids
plat500_id = 1078761063681630361
gold500_id = 1078760915312320573
silver500_id = 1078760773809090600
copper500_id = 1078760480362999978


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


is_t50_room = partial(is_channel, id_=t50_room_id)
is_meme_room = partial(is_channel, id_=meme_room_id)
is_testing_room = partial(is_channel, id_=testing_room_id)
is_helpers_room = partial(is_channel, id_=helpers_room_id)
is_player_id_please_room = partial(is_channel, id_=1117867265375879259)
is_role_count_room = partial(is_channel, id_=role_count_room_id)


def is_098799(author):
    return author.id == id_098799


def is_andreas(author):
    return author.id == id_andreas

def is_fishy(author):
    return author.id == id_fishy #super tiner author 😂


def get_safe_league_prefix(league):
    return league[:-1]


async def role_prefix_and_only_tourney_roles_check(role, safe_league_prefix):
    return role.name.strip().startswith(safe_league_prefix) and "500" in role.name.strip()


position_role_ids = {
    1: top1_id,
    10: top10_id,
    25: top25_id,
    50: top50_id,
    100: top100_id,
    200: top200_id,
    300: top300_id,
    400: top400_id,
    500: top500_id,
    600: top600_id,
    700: top700_id,
    800: top800_id,
    900: top900_id,
    1000: top1000_id,
    1500: top1500_id,
    2000: top2000_id,
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
