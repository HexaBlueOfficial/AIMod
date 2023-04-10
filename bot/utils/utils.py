import discord
import typing
import aiohttp
import json
import re
import random
from . import errors

async def add_guild(auth: str, guild: discord.Guild) -> typing.Dict[str, typing.Any]:
    """
    Adds a Guild to the database.

    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild to add.
    @type guild: discord.Guild
    """

    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://aimod.hexa.blue/api/guilds", json={
            "id": guild.id
        }) as response:
            response = await response.json()

    return response

async def remove_guild(auth: str, guild: discord.Guild) -> typing.Dict[str, typing.Any]:
    """
    Removes a Guild from the database.

    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild to remove.
    @type guild: discord.Guild
    """

    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.delete(f"https://aimod.hexa.blue/api/guilds/{guild.id}") as response:
            response = await response.json()

    return response

async def get_guild(guild: discord.Guild) -> typing.Dict[str, typing.Union[str, int]]:
    """
    Gets a Guild's configuration.

    @param guild: The Guild to get.
    @type guild: discord.Guild
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://aimod.hexa.blue/api/guilds/{guild.id}") as response:
            response = await response.json()

    return response

async def edit_config(auth: str, guild: discord.Guild, lang: str=None, openai: str=None, scale_max: int=None, actions: typing.List[str]=None, log_mod: discord.TextChannel=None, log_flag: discord.TextChannel=None) -> typing.Dict[str, typing.Union[str, int]]:
    """
    Modifies the Guild's full configuration.
    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild to modify the configuration of.
    @type guild: discord.Guild
    @param lang: The language.
    @type lang: typing.Optional[str]
    @param openai: The OpenAI API key to use.
    @type openai: typing.Optional[str]
    @param log_mod: The channel for moderation logs.
    @type log_mod: typing.Optional[discord.TextChannel]
    @param log_flag: The channel for flagged message logs.
    @type log_flag: typing.Optional[discord.TextChannel]
    """

    if lang is None and openai is None and log_mod is None and log_flag is None:
        raise errors.AtLeastOneEdit
    
    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.patch(f"https://aimod.hexa.blue/api/guilds/{guild.id}", json={
            "lang": lang,
            "openai": openai,
            "log_mod": log_mod.id if log_mod is not None else None,
            "log_flag": log_flag.id if log_flag is not None else None
        }) as response:
            response = await response.json()

    return response

def extract_lines(lang: str) -> typing.Dict[str, str]:
    """
    Extracts lines from the language string.

    @param lang: The language string.
    @type lang: str
    """

    with open(f"./AIMod/bot/json/lang/{lang.lower()}.json") as langfile:
        lines: typing.Dict[str, str] = json.load(langfile)

    return lines

async def init_cmd(guild: discord.Guild) -> typing.Tuple[typing.Dict[str, str], str]:
    """
    Returns a (lines, openai) tuple, needed for most commands.

    @param guild: The Guild where the command is being ran.
    @type guild: discord.Guild
    """

    config = await get_guild(guild)

    lines = extract_lines(config["lang"])

    return (lines, config["openai"])

async def add_warning(auth: str, guild: discord.Guild, user: discord.Member, mod: discord.Member, reason: str=None) -> typing.Dict[str, typing.Any]:
    """
    Adds a warning to the database.

    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild where the warning is issued.
    @type guild: discord.Guild
    @param user: The warned user.
    @type user: discord.Member
    @param reason: The warning reason.
    @type reason: typing.Optional[str]
    """

    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f"https://aimod.hexa.blue/api/guilds/{guild.id}/warns", json={
            "user": user.id,
            "mod": mod.id,
            "reason": reason
        }) as response:
            response = await response.json()

    return response

async def remove_warning(auth: str, warn_id: int) -> typing.Dict[str, typing.Any]:
    """
    Removes a warning.

    @param auth: Authorization key.
    @type auth: str
    @param warn_id: The warning's ID.
    @type warn_id: int
    """

    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.delete(f"https://every.hexa.blue/api/warns/{warn_id}") as response:
            response = await response.json()

    try:
        return response["error"]
    except KeyError:
        return response

def prepare_gpt(config: typing.Dict[str, typing.Union[str, int]]):
    """
    Prepares `await utils.gpt_msg()` and `await utils.gpt_nick()`.

    @param config: Guild configuration.
    @type config: typing.Dict[str, typing.Union[str, int]]
    """

    lines = extract_lines(config["lang"])
    openai = None
    if config["openai"] is not None:
        openai = config["openai"]
    else:
        raise errors.NoOpenAIKey
    rules = None
    if config["rules"] is not None:
        rules = config["rules"]
    else:
        raise errors.NoRules
    scale_max = config["scale_max"]

    rls = ""
    for rule in rules:
        rls += f"• {rule}\n"
    rls = rls.rstrip()

    return lines, openai, rls, scale_max

async def gpt_msg(config: typing.Dict[str, typing.Union[str, int]], messages: typing.List[discord.Message]) -> str:
    """
    Sends messages to GPT-3.5-turbo.

    @param config: The Guild where the messages were sent's configuration, found through `await utils.get_guild()`.
    @type config: typing.Dict[str, typing.Union[str, int]]
    @param messages: The list of messages to send.
    @type messages: typing.List[discord.Message]
    """

    lines, openai, rls, scale_max = prepare_gpt(config)

    contents = []
    for message in messages:
        contents.append(message.content)
    
    msgs = ""
    for content in contents:
        msgs += f"{content}\n"
    msgs = msgs.rstrip()

    headers = {"Authorization": f"Bearer {openai}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json={
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": lines["GPT"]["MESSAGES"].replace("{rls}", rls).replace("{msgs}", msgs).replace("{scale_max}", scale_max)
            }]
        }) as response:
            response = await response.json()
    
    return response["choices"][0]["message"]["content"]

async def gpt_nick(config: typing.Dict[str, typing.Union[str, int]], nickname: str) -> str:
    """
    Sends a nickname to GPT-3.5-turbo.

    @param config: The Guild where the nickname was found's configuration, found through `await utils.get_guild()`.
    @type config: typing.Dict[str, typing.Union[str, int]]
    @param nickname: The nickname to send.
    @type nickname: str
    """

    lines, openai, rls, scale_max = prepare_gpt(config)

    headers = {"Authorization": f"Bearer {openai}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json={
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": lines["GPT"]["NICKNAME"].replace("{rls}", rls).replace("{nick}", nickname).replace("{scale_max}", scale_max)
            }]
        }) as response:
            response = await response.json()
    
    return response["choices"][0]["message"]["content"]

def process_gpt(gpt: str) -> typing.List[typing.Dict[str, typing.Union[str, int]]]:
    """
    Processes GPT-3.5-turbo's response to take eventual action.

    @param gpt: GPT-3.5-turbo's response.
    @type gpt: str
    """

    try:
        ratingstr = re.search("`(.+?)`", gpt).group(1)
    except AttributeError:
        raise errors.GPTResponseProcessingFailed

    ratingstr = ratingstr.strip("`")

    ratings = ratingstr.split("\n")

    ratingsx: typing.List[typing.Dict[str, typing.Union[str, int]]] = []
    for rating in ratings:
        ratingspl = rating.split(" - ")

        try:
            ratingspl[1] = int(ratingspl[1])
        except:
            ratingspl[1] = int(ratingspl[1].split()[0])

        ratingsx.append({
            "content": ratingspl[0],
            "rating": int(ratingspl[1])
        })
    
    return ratingsx

def make_embed(title: str, description: str=None, thumbnail: str=None, image: str=None, fields: typing.List[list]=None) -> discord.Embed:
    """
    Makes an Embed!

    @param title: Embed title.
    @type title: str
    @param description: Embed description.
    @type description: typing.Optional[str]
    @param thumbnail: Embed thumbnail image URL.
    @type thumbnail: typing.Optional[str]
    @param image: Embed image URL.
    @type image: typing.Optional[str]
    @param fields: Embed fields, in [name, value, inline] format.
    @type fields: typing.Optional[typing.List[list]]
    """

    with open("./Agostino/bot/json/embed.json") as embedfile:
        embed: typing.Dict[str, str] = json.load(embedfile)
    
    e = discord.Embed(title=title, color=int(embed["color"], 16), description=description)
    e.set_author(name=embed["author"], icon_url=embed["icon"])
    if thumbnail is not None:
        e.set_thumbnail(url=thumbnail)
    if fields is not None:
        for field in fields:
            try:
                field[2]
            except IndexError:
                field.append(False)

            e.add_field(name=field[0], value=field[1], inline=field[2])
    if image is not None:
        e.set_image(url=image)
    e.set_footer(text=embed["footer"], icon_url=embed["icon"])

    return e

def random_presence(bot: discord.Client) -> discord.Activity:
    """
    Gets a random presence.

    @param bot: The Client instance (for special presences).
    @type bot: discord.Client
    """

    with open("./AIMod/bot/json/presence.json") as presencefile:
        presence: typing.Dict[str, typing.Dict[str, str]] = json.load(presencefile)
    
    randtype: typing.List[typing.List[str], discord.ActivityType] = random.choice([[presence["playing"], discord.ActivityType.playing], [presence["watching"], discord.ActivityType.watching]])
    i = random.randint(0, len(randtype[0]) - 1)

    randtype[0][i] = randtype[0][i].replace("{u}", bot.users).replace("{g}", bot.guilds)

    activity = discord.Activity(name=randtype[0][i], type=randtype[1])

    return activity