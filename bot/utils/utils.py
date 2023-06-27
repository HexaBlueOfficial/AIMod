import discord
import aiohttp
import json
import re
import random
from typing import *
from . import errors, views

async def add_guild(auth: str, guild: discord.Guild) -> Dict[str, Any]:
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

async def remove_guild(auth: str, guild: discord.Guild) -> Dict[str, Any]:
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

async def get_guild(guild: discord.Guild) -> Dict[str, Any]:
    """
    Gets a Guild's configuration.

    @param guild: The Guild to get.
    @type guild: discord.Guild
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://aimod.hexa.blue/api/guilds/{guild.id}") as response:
            response = await response.json()

    return response

async def edit_config(auth: str, guild: discord.Guild, *, lang: str, openai: str, scale_max: int, log_mod: discord.TextChannel, log_flag: discord.TextChannel) -> Dict[str, Union[str, int]]:
    """
    Modifies the Guild's full configuration.
    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild to modify the configuration of.
    @type guild: discord.Guild
    @param lang: The language.
    @type lang: Optional[str]
    @param openai: The OpenAI API key to use.
    @type openai: Optional[str]
    @param scale_max: The highest number for the rating scale.
    @type scale_max: Optional[int]
    @param log_mod: The channel for moderation logs.
    @type log_mod: Optional[discord.TextChannel]
    @param log_flag: The channel for flagged message logs.
    @type log_flag: Optional[discord.TextChannel]
    """

    if lang is None and openai is None and scale_max is None and log_mod is None and log_flag is None:
        raise errors.AtLeastOneEdit
    
    headers = {"auth": f"{auth}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.patch(f"https://aimod.hexa.blue/api/guilds/{guild.id}", json={
            "lang": lang,
            "openai": openai,
            "scale_max": scale_max,
            "log_mod": log_mod.id if log_mod is not None else None,
            "log_flag": log_flag.id if log_flag is not None else None
        }) as response:
            response = await response.json()

    return response

def extract_lines(lang: str) -> Dict[str, str]:
    """
    Extracts lines from the language string.

    @param lang: The language string.
    @type lang: str
    """

    with open(f"./AIMod/bot/json/lang/{lang.lower()}.json") as langfile:
        lines: Dict[str, str] = json.load(langfile)

    return lines

async def get_config(guild: discord.Guild) -> Tuple[Dict[str, str], str, List[str], int, List[Literal["NONE", "FLAG", "DELETE", "WARN", "DELETE_WARN"]], int, int]:
    """
    Returns a (lines, openai, rules, scale_max, actions) tuple, in other words a processed version of the Guild's configuration.

    @param guild: The Guild to get the configuration of.
    @type guild: discord.Guild
    """

    config = await get_guild(guild)
    
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
    actions = config["actions"]
    log_mod = config["log_mod"]
    log_flag = config["log_flag"]

    return lines, openai, rules, scale_max, actions, log_mod, log_flag

async def add_warning(auth: str, guild: discord.Guild, user: discord.Member, mod: discord.Member, *, reason: str) -> Dict[str, Any]:
    """
    Adds a warning to the database.

    @param auth: Authorization key.
    @type auth: str
    @param guild: The Guild where the warning is issued.
    @type guild: discord.Guild
    @param user: The warned user.
    @type user: discord.Member
    @param reason: The warning reason.
    @type reason: Optional[str]
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

async def remove_warning(auth: str, warn_id: int) -> Dict[str, Any]:
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

def prepare_gpt(config: Tuple[Dict[str, str], str, List[str], int, List[Literal["NONE", "FLAG", "DELETE", "WARN", "TIMEOUT", "WARN_TIMEOUT", "DELETE_WARN", "DELETE_TIMEOUT", "DELETE_WARN_TIMEOUT"]], int, int]) -> Tuple[Dict[str, str], str, str, int]:
    """
    Prepares `await utils.gpt_msg()` and `await utils.gpt_nick()`.

    @param config: Processed Guild configuration.
    @type config: Tuple[Dict[str, str], str, List[str], int, List[Literal["NONE", "FLAG", "DELETE", "WARN", "TIMEOUT", "WARN_TIMEOUT", "DELETE_WARN", "DELETE_TIMEOUT", "DELETE_WARN_TIMEOUT"]], int, int]
    """

    lines, openai, rules, scale_max = config
    
    rls = ""
    for rule in rules:
        rls += f"• {rule}\n"
    rls = rls.rstrip()

    return lines, openai, rls, scale_max

async def gpt(prep: Tuple[Dict[str, str], str, str, int], *, messages: List[discord.Message], nick: str) -> str:
    """
    Sends messages to GPT-3.5-turbo.

    @param prep: GPT preparation, found through `utils.prepare_gpt()`.
    @type prep: Tuple[Dict[str, str], str, str, int]
    @param messages: The list of messages to send.
    @type messages: Optional[List[discord.Message]]
    @param nick: The nickname to send.
    @type nick: Optional[str]
    """

    lines, openai, rls, scale_max = prep

    gptcontent = ""
    if messages is not None:
        msgs = ""
        for message in messages:
            msgs += f"{message.content}\n"
        msgs = msgs.rstrip()

        gptcontent = lines["GPT"]["MESSAGES"].replace("{rls}", rls).replace("{msgs}", msgs).replace("{scale_max}", scale_max)
    elif nick is not None:
        gptcontent = lines["GPT"]["NICKNAME"].replace("{rls}", rls).replace("{nick}", nick).replace("{scale_max}", scale_max)

    headers = {"Authorization": f"Bearer {openai}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json={
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": gptcontent
            }]
        }) as response:
            response = await response.json()
    
    return response["choices"][0]["message"]["content"]

def process_gpt(gpt: str) -> List[Dict[str, Union[str, int]]]:
    """
    Processes GPT-3.5-turbo's response.

    @param gpt: GPT-3.5-turbo's response.
    @type gpt: str
    """

    try:
        ratingstr = re.search("`(.+?)`", gpt).group(1)
    except AttributeError:
        raise errors.GPTResponseProcessingFailed

    ratingstr = ratingstr.strip("`")

    ratings = ratingstr.split("\n")

    ratingsx: List[Dict[str, Union[str, int]]] = []
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

async def aimod(bot: discord.Client, guild: discord.Guild, *, messages: List[discord.Message], member: discord.Member) -> List[Dict[str, Union[str, int]]]:
    """
    Sends request to GPT-3.5-turbo and takes action.

    @param bot: The Client instance, to take actions.
    @type bot: discord.Client
    @param guild: The Guild the message(s) or nickname was found.
    @type guild: discord.Guild
    @param messages: The messages that will be sent to GPT-3.5-turbo.
    @type messages: Optional[List[discord.Message]]
    @param member: The Member using the nickname that will be sent to GPT-3.5-turbo.
    @type member: Optional[discord.Member]
    """

    if messages is not None and member is not None:
        raise errors.BothMessagesAndNick
    
    config = await get_config(guild)
    prep = prepare_gpt(config)

    gptres = await gpt(prep, messages=messages, nick=member.nick)
    ratings = process_gpt(gptres)

    lines, openai, rules, scale_max, actions, log_mod, log_flag = config

    with open("./AIMod/bot/json/embed.json") as embedfile:
        embed: Dict[str, str] = json.load(embedfile)

    for rating in ratings:
        message = messages[ratings.index(rating)] if messages is not None else None

        match actions[rating["rating"]]:
            case "NONE":
                rating["action"] = "NONE"
            case "FLAG":
                rating["action"] = "FLAG"

                log = bot.get_channel(log_flag)

                e = discord.Embed(title=lines["log"]["flag"]["title"].replace("{x}", lines["message"] if message is not None else lines["nickname"]), color=0xff8800, description=rating["content"])
                e.set_author(name=str(message.author) if message is not None else str(member), icon_url=message.author.avatar.url if message is not None else member.avatar.url)
                e.set_thumbnail(url="https://aimod.hexa.blue/images/flag.png")
                if message is not None:
                    e.add_field(name=lines["log"]["flag"]["message_info"]["name"], value=lines["log"]["flag"]["message_info"]["value"].replace("{id}", message.id).replace("{channel}", f"{message.channel.mention} (`{message.channel.id}`)"))
                e.set_footer(text=embed["footer"], icon_url=embed["icon"])
                await log.send(embed=e, view=views.FlagLog())
            case "DELETE":
                rating["action"] = "DELETE"

                log = bot.get_channel(log_mod)

                e = discord.Embed(title=lines["log"]["delete"]["title"].replace("{x}", lines["message"] if message is not None else lines["nickname"]), color=0xff3b3b, description=rating["content"])
                e.set_author(name=str(message.author) if message is not None else str(member), icon_url=message.author.avatar.url if message is not None else member.avatar.url)
                e.set_thumbnail(url="https://aimod.hexa.blue/images/flag.png")
                if message is not None:
                    e.add_field(name=lines["log"]["delete"]["message_info"]["name"], value=lines["log"]["delete"]["message_info"]["value"].replace("{id}", message.id).replace("{channel}", f"{message.channel.mention} (`{message.channel.id}`)"))
                e.set_footer(text=embed["footer"], icon_url=embed["icon"])
                await log.send(embed=e, view=views.DeleteLog())

                if message is not None: await message.delete()
                else: await member.edit(nick="")
            case "WARN":
                rating["action"] = "WARN"

                log = bot.get_channel(log_mod)

                e = discord.Embed(title=lines["log"]["warn"]["title"], color=0xff3b3b, description=rating["content"])
                e.set_author(name=str(message.author) if message is not None else str(member), icon_url=message.author.avatar.url if message is not None else member.avatar.url)
                e.set_thumbnail(url="https://aimod.hexa.blue/images/flag.png")
                e.set_footer(text=embed["footer"], icon_url=embed["icon"])
                await log.send(embed=e, view=views.WarnLog())
            case "DELETE_WARN":
                rating["action"] = "DELETE_WARN"
    
    return ratings

def make_embed(title: str, *, description: str, thumbnail: str, image: str, fields: List[list]) -> discord.Embed:
    """
    Makes an Embed!

    @param title: Embed title.
    @type title: str
    @param description: Embed description.
    @type description: Optional[str]
    @param thumbnail: Embed thumbnail image URL.
    @type thumbnail: Optional[str]
    @param image: Embed image URL.
    @type image: Optional[str]
    @param fields: Embed fields, in [name, value, inline] format.
    @type fields: Optional[List[list]]
    """

    with open("./AIMod/bot/json/embed.json") as embedfile:
        embed: Dict[str, str] = json.load(embedfile)

    e = discord.Embed(title=title, color=int(embed["color"], 16), description=description)
    e.set_author(name=embed["author"], icon_url=embed["icon"])
    if thumbnail is not None:
        e.set_thumbnail(url=thumbnail)
    if fields is not None:
        for field in fields:
            try:
                field[2]
            except IndexError:
                field.append(True)

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
        presence: Dict[str, Dict[str, str]] = json.load(presencefile)
    
    randtype: List[List[str], discord.ActivityType] = random.choice([[presence["playing"], discord.ActivityType.playing], [presence["watching"], discord.ActivityType.watching]])
    i = random.randint(0, len(randtype[0]) - 1)

    randtype[0][i] = randtype[0][i].replace("{u}", bot.users).replace("{g}", bot.guilds)

    activity = discord.Activity(name=randtype[0][i], type=randtype[1])

    return activity