import discord
import utils
import json
import typing
import aiohttp
from discord import app_commands as app
from discord.ext import tasks

bot = discord.Client(intents=discord.Intents.all())
tree = app.CommandTree(bot)

with open("./token.json") as tokenfile:
    token = json.load(tokenfile)

@bot.event
async def on_ready():
    flamey = bot.get_user(450678229192278036)
    await flamey.dm_channel.send(f"**AIMod** is ready and running on **discord.py {discord.__version__}**!")

@bot.event
async def on_guild_join(guild: discord.Guild):
    await utils.add_guild(token["aimod"], guild)

    lines = utils.extract_lines("EN")

    owner = guild.owner.dm_channel if not None else await guild.owner.create_dm()

    e = utils.make_embed(lines["intro"]["title"],
        description=lines["intro"]["desc"],
        fields=[
            [lines["intro"]["set_key"]["name"], lines["intro"]["set_key"]["value"], False],
            [lines["intro"]["set_lang"]["name"], lines["intro"]["set_lang"]["value"], False],
            [lines["intro"]["set_logs"]["name"], lines["intro"]["set_logs"]["value"], False],
        ])

bot.run(token["aimod"])