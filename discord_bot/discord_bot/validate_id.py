import logging
import re

import easyocr
from asgiref.sync import sync_to_async

from discord_bot.util import get_tower, get_verified_role, verified_role_id
from dtower.sus.models import KnownPlayer, PlayerId

hex_digits = set("0123456789abcdef")
reader = easyocr.Reader(["en"])


def only_made_of_hex(message):
    player_id_candidate = message.content.strip().lower()
    contents = set(player_id_candidate)
    return contents | hex_digits == hex_digits


def hamming_distance(s1, s2):
    """0 if identical, 1 if completely different"""
    if len(s1) != len(s2):
        raise ValueError("Strings must be of equal length")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2)) / len(s1)


async def check_image(content, image_bytes):
    ocr_results = reader.readtext(image_bytes)

    player_id_candidates = []

    for _, line, _ in ocr_results:
        subresult = [item for item in re.findall(r"\S{16}", line) if "uppor" not in item]

        if subresult:
            player_id_candidates.append(subresult[0])

    passes_score = any([hamming_distance(candidate, content) < 0.2 for candidate in player_id_candidates])

    if not passes_score:
        logging.info(f"{content}\n\n{player_id_candidates}\n\n{ocr_results}")

    return passes_score


async def validate_player_id(client, message):
    if message.author.id in [96626874708430848, 778131594132062240, 778131594132062240]:
        return

    try:
        if len(message.content) == 16 and message.attachments and only_made_of_hex(message):
            image_bytes = await message.attachments[0].read()

            if not (await check_image(message.content, image_bytes)):
                await message.add_reaction("⁉️")
                await message.add_reaction("🖼️")
                return

            discord_id = message.author.id

            player, created = await sync_to_async(KnownPlayer.objects.get_or_create, thread_sensitive=True)(
                discord_id=discord_id, defaults=dict(approved=True, name=message.author.name)
            )
            await sync_to_async(PlayerId.objects.update_or_create, thread_sensitive=True)(
                id=message.content.upper(), player_id=player.id, defaults=dict(primary=True)
            )
            discord_player = await (await get_tower(client)).fetch_member(player.discord_id)
            await handle_role_present(client, discord_player)
            await message.add_reaction("✅")
        else:
            await message.add_reaction("⁉️")
    except Exception as exc:
        await message.channel.send(f"Something went terribly wrong, please debug me. \n\n {exc}")
        raise exc


async def handle_role_present(client, discord_player):
    verified_role = await get_verified_role(client)

    has_player_id_present_role = [role for role in discord_player.roles if role.id == verified_role_id]

    if not has_player_id_present_role:
        await discord_player.add_roles(verified_role)
