import logging

from discord_bot.util import get_tower, id_098799, testing_room_id


async def remove_nicknames(client, channel=None):
    tower = await get_tower(client)
    channel = channel if channel else client.fetch_channel(testing_room_id)

    success = 0
    failure = 0

    await channel.send("Starting to remove nicknames from people...")

    # for member in [await tower.fetch_member(id_098799)]:  # uncomment me to test
    async for member in tower.fetch_members():
        try:
            await member.edit(nick=None)
            success += 1
        except Exception:
            await channel.send(f"😱😱😱 Failed to remove nickname from {member}, continuing...")
            failure += 1

        if (success + failure) % 500 == 0:
            await channel.send(f"Removed {success=} {failure=}")

        if (success + failure) % 10 == 0:
            logging.info(f"{success=} {failure=}")

    await channel.send(f"Finished removing nicknames from people, {success=}, {failure=}")
