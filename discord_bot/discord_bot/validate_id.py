from asgiref.sync import sync_to_async

from discord_bot.util import get_tower, get_verified_role, verified_role_id
from dtower.sus.models import KnownPlayer, PlayerId

hex_digits = set("0123456789abcdef")


def only_made_of_hex(message):
    player_id_candidate = message.content.strip().lower()
    contents = set(player_id_candidate)
    return contents | hex_digits == hex_digits


async def validate_player_id(client, message):
    try:
        if 17 > len(message.content) > 12 and message.attachments and only_made_of_hex(message):
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
