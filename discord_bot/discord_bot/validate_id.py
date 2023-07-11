from asgiref.sync import sync_to_async

from discord_bot.util import get_tower, get_verified_role, verified_role_id
from dtower.sus.models import KnownPlayer, PlayerId


async def validate_player_id(client, message):
    try:
        if 17 > len(message.content) > 12 and message.attachments:
            player, created = await sync_to_async(KnownPlayer.objects.get_or_create, thread_sensitive=True)(
                discord_id=message.author.id, defaults=dict(approved=True, name=message.author.name)
            )
            await sync_to_async(PlayerId.objects.update_or_create, thread_sensitive=True)(id=message.content, player_id=player.id, defaults=dict(primary=True))
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
