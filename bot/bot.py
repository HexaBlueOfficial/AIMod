import discord
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
    ...

bot.run(token["aimod"])