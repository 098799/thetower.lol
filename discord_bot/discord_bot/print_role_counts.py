from collections import defaultdict

from discord_bot.util import get_all_members, get_tower
import const


async def print_roles(client, message):
    skip_roles = {
        "⭐Pogs Blue⭐",
        "Bots",
        "Dyno",
        "ServerStats",
        "YAGPDB.xyz",
        "Ticket Tool",
        "Patron Logger",
        "MEE6",
        "Giveaway Boat",
        "ProBot ✨",
        "TechTreeTourneyBot",
        "See Nothing",
        "role_bot",
        "🔶️Head mods🔶️",
        "🔶️Mods🔶️",
        "🔶️Retired Mods🔶️",
        "🔶️Jr Mods🔶️",
        "PUNisher",
        "RFole",
        "Emoji",
        "AllChannelsAccess",
        "No Tickets",
        ",",
        "Google Bot",
        "@everyone",
    }

    members = await get_all_members(client)

    # all_roles = {role for member in members for role in member.roles}
    # all_positions = sorted([(role.position, role) for role in all_roles])

    role_counts = defaultdict(int)

    for member in members:
        for role in member.roles:
            role_counts[(role.position, role.name)] += 1

    role_counts = sorted([(k[0], k[1], v) for k, v in role_counts.items() if k[1] not in skip_roles], reverse=True)

    role_types_to_show = [role_type for role_type in message.content.split()[1:]]

    roles_allowed = []

    if "top" in role_types_to_show:
        roles_allowed += [(number, role, count) for number, role, count in role_counts if role.startswith("Top")]

    if "tourney" in role_types_to_show:
        roles_allowed += [
            (number, role, count)
            for number, role, count in role_counts
            if "Highest position" in role
            or role.startswith("Platinum ")
            or role.startswith("Gold ")
            or role.startswith("Silver ")
            or role.startswith("Copper ")
        ]

    if "uw" in role_types_to_show:
        roles_allowed += [
            (number, role, count)
            for number, role, count in role_counts
            if role.startswith("Chain ")
            or role.startswith("Smart ")
            or role.startswith("Death ")
            or role.startswith("Chrono ")
            or role.startswith("Inner ")
            or role.startswith("Golden To")
            or role.startswith("Poison ")
            or role.startswith("Black Ho")
            or role.startswith("Spotlight")
        ]

    if "bot" in role_types_to_show:
        roles_allowed += [
            (number, role, count)
            for number, role, count in role_counts
            if role.startswith("Golden Bot") or role.startswith("Flame Bot") or role.startswith("Thunder Bot") or role.startswith("Amplify Bot")
        ]

    if "stats" in role_types_to_show:
        roles_allowed += [
            (number, role, count)
            for number, role, count in role_counts
            if role.endswith(" Club")
            or role.startswith("Coins ")
            or role.startswith("Researches ")
            or role.startswith("Cash ")
            or role.startswith("Stones ")
            or role.startswith("Waves ")
            or role.startswith("Module ")
            or "Turtle" in role
            or "Blender" in role
            or "eHP" in role
            or "Hybrid" in role
            or "Devo" in role
            or "Glass Cannon" in role
            or "Infinity and Beyond" in role
            or "Year Role" in role
        ]

    if "milestone" in role_types_to_show:
        roles_allowed += [(number, role, count) for number, role, count in role_counts if role.startswith("Milestone ")]

    if "pack" in role_types_to_show:
        roles_allowed += [
            (number, role, count)
            for number, role, count in role_counts
            if role.startswith("Epic Pack") or role.startswith("Starter-Pack") or role.startswith("No Ads")
        ]

    channel = await client.fetch_channel(const.role_count_channel_id)

    chunk_size = 15

    for role_chunk in range(len(roles_allowed) // chunk_size + 1):
        role_list_chunk = roles_allowed[role_chunk * chunk_size : (role_chunk + 1) * chunk_size]
        role_counts_normalized = "\n".join([f"{role}: {count}" for _, role, count in role_list_chunk])

        await channel.send(role_counts_normalized)
