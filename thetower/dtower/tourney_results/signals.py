import os

import discord
from django.db.models.signals import post_save
from django.dispatch import receiver

from discord_bot.util import is_testing_channel
from dtower.tourney_results.constants import champ
from dtower.tourney_results.models import TourneyResult

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)


@client.event
async def on_ready():
    channel = await client.fetch_channel(is_testing_channel)
    await channel.send("🚀 https://thetower.lol/ has been updated with tourney results.")
    await client.close()


@receiver(post_save, sender=TourneyResult)
def recalculate_results(sender, instance, signal, created, update_fields, raw, using, **kwargs):
    if instance.public == False:
        # subprocess.call("systemctl restart streamlit", shell=True)
        ...
    else:
        return
        if instance.league == champ:
            if instance.public == True:  # result release to the public
                client.run(os.getenv("DISCORD_TOKEN"))

            # if bcs := instance.conditions.all():
            #     other_results = TourneyResult.objects.filter(~Q(league__in=[champ, copper]), date=instance.date)

            #     for result in other_results:
            #         result.conditions.clear()

            #         for bc in bcs:
            #             result.conditions.add(bc)

            # subprocess.call("systemctl restart streamlit2", shell=True)
            # subprocess.call("systemctl restart streamlit", shell=True)
