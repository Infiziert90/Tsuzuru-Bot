import shlex
import aiohttp
import uvloop
import asyncio
import discord
import logging
import argparse
import commands
import datetime
from cmd_manager import dispatcher
from config import config, help_text
from typing import Union
from cmd_manager.bot_args import parser, HelpException, UnkownCommandException
from handle_messages import private_msg_code, delete_user_message, send_log_message
from commands.vote_command import add_vote, remove_vote, ongoing_votes, anon_votes
from commands.role_system import roles, role_handler
from cmd_manager.filters import EX_SERVER, EX_WELCOME_CHANNEL
from utils import user_roles

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

client = discord.Client()
commands.load_commands()


@client.event
async def on_ready():
    logging.info(f'Logged in as\nUsername: {client.user.name}\nID: {client.user.id}\nAPI Version: {discord.__version__}')
    gameplayed = discord.Game(name=config.MAIN.get("gameplayed", "Yuri is Love!"))
    await client.change_presence(activity=gameplayed)


@client.event
async def on_message(message: discord.Message):
    await handle_commands(message)


@client.event
async def on_message_edit(_: discord.Message, message: discord.Message):
    await handle_commands(message)


@client.event
async def on_member_join(mem: discord.Member):
    if mem.guild.id == EX_SERVER:
        await send_log_message(f"{mem.display_name} has joined the server", discord.Embed.Empty, mem, discord.Colour.green(), client)
        channel = client.get_channel(EX_WELCOME_CHANNEL)
        mention = await channel.send(f"<@!{mem.id}>")
        member_message = await channel.send(embed=discord.Embed(description=help_text("bot_bot", "member_join"), color=333333))
        await asyncio.sleep(300)
        await delete_user_message(member_message)
        await delete_user_message(mention)


@client.event
async def on_member_remove(mem: discord.Member):
    if mem.guild.id == EX_SERVER:
        await send_log_message(f"{mem.display_name} has left the server", discord.Embed.Empty, mem, discord.Colour.red(), client)


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.guild.id == EX_SERVER:
        if before.nick != after.nick:
            await send_log_message(f"{before.display_name if before.nick is None else before.nick} changed their nickname",
                                   f"New nickname {after.nick}", after, discord.Colour.blue(), client)
        elif before.name != after.name:
            await send_log_message(f"{before.name} changed their username", f"New username {after.name}", after, discord.Colour.orange(), client)


@client.event
async def on_reaction_remove(reaction: discord.Reaction, user: Union[discord.User, discord.Member]):
    if not reaction.me or user.id == client.user.id:
        return

    if reaction.message.id in ongoing_votes:
        await remove_vote(reaction, user, ongoing_votes)


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: Union[discord.User, discord.Member]):
    if not reaction.me or user.id == client.user.id:
        return

    if reaction.message.id in ongoing_votes:
        await add_vote(reaction, user, ongoing_votes)
    elif reaction.message.id in anon_votes:
        await add_vote(reaction, user, anon_votes)

        
@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == client.user.id:
        return

    if payload.guild_id == EX_SERVER and payload.channel_id == EX_WELCOME_CHANNEL:
        if payload.emoji.name in roles:
            member = client.get_guild(payload.guild_id).get_member(payload.user_id)
            await role_handler(member, payload.emoji.name, remove=False)


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == client.user.id:
        return

    if payload.guild_id == EX_SERVER and payload.channel_id == EX_WELCOME_CHANNEL:
        if payload.emoji.name in roles:
            member = client.get_guild(payload.guild_id).get_member(payload.user_id)
            await role_handler(member, payload.emoji.name, remove=True)


async def handle_commands(message: discord.Message):
    is_guild = isinstance(message.channel, discord.abc.GuildChannel)
    if message.author.id == client.user.id:  # own bot
        return

    if message.author.id in user_roles:
        return

    if not is_guild and message.content[:11] != ">>getnative":
        return await message.author.send("Forbidden, sorry")

    if is_guild and message.guild.id == EX_SERVER:
        if message.channel.id == EX_WELCOME_CHANNEL:
            await delete_user_message(message)  # no return here

    if not message.content.startswith(">>") or len(message.content) == 2:  # prevent forwarding '>>' messages
        return

    if is_guild:
        today = datetime.datetime.today().strftime("%a %d %b %H:%M:%S")
        logging.info(f"Date: {today} User: {message.author} Server: {message.guild.name} "
                     f"Channel: {message.channel.name} Command: {message.content[:50]}")

    try:
        arg_string = message.clean_content[2:]
        arg_string = shlex.split(message.clean_content[2:])
        args = parser.parse_args(arg_string)
    except ValueError as err:
        return await private_msg_code(message, str(err))
    except HelpException as err:
        await delete_user_message(message)
        return await private_msg_code(message, str(err))
    except (UnkownCommandException, argparse.ArgumentError) as err:
        if arg_string[0] in dispatcher.commands:
            return await private_msg_code(message, str(err))
        return

    return await dispatcher.handle(args.command, client, message, args)


def main():
    while True:
        try:
            logging.info("Start discord run")
            # bot-Bot
            client.run(config.MAIN.login_token)
            # Test-Bot
            # client.run(config.MAIN.test_token)
        except aiohttp.ClientConnectorError:
            continue
        except KeyboardInterrupt:
            return loop.close()


if __name__ == "__main__":
    main()
