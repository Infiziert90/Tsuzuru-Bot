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
from cmd_manager.bot_args import parser, HelpException, UnkownCommandException
from handle_messages import private_msg_code, delete_user_message, send_log_message
from commands.vote_command import ongoing_votes, Vote
from commands.role_system import roles, role_handler
from cmd_manager.filters import EX_SERVER, EX_WELCOME_CHANNEL
from utils import prison_inmates, check_and_release

uvloop.install()
loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

client = discord.Client()
commands.load_commands()


@client.event
async def on_ready():
    logging.info(f'Logged in as\nUsername: {client.user.name}\nID: {client.user.id}\nAPI: {discord.__version__}')
    await client.change_presence(activity=discord.Game(name=config.MAIN.get("gameplayed", "Yuri is Love!")))


@client.event
async def on_message(message: discord.Message):
    await handle_commands(message)


@client.event
async def on_message_edit(_: discord.Message, message: discord.Message):
    await handle_commands(message)


@client.event
async def on_member_join(mem: discord.Member):
    if mem.guild.id == EX_SERVER:
        await send_log_message(client, mem, f"{mem.display_name} has joined the server")
        channel = client.get_channel(EX_WELCOME_CHANNEL)
        mention = await channel.send(f"<@!{mem.id}>")
        text = help_text("bot_bot", "welcome_set")["member_join"]
        member_mes = await channel.send(embed=discord.Embed(description=text, color=333333))
        await asyncio.sleep(300)
        await delete_user_message(member_mes)
        await delete_user_message(mention)


@client.event
async def on_member_remove(mem: discord.Member):
    if mem.guild.id == EX_SERVER:
        await send_log_message(client, mem, f"{mem.display_name} has left the server", colour=discord.Colour.red())


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.guild.id != EX_SERVER:
        return

    if before.nick != after.nick:
        await send_log_message(client, after, f"{before.display_name if before.nick is None else before.nick} "
                               f"changed their nickname", f"New nickname is {after.nick}",
                               colour=discord.Colour.blue())
    elif before.name != after.name:
        await send_log_message(client, after, f"{before.name} changed their username", f"New username is {after.name}",
                               colour=discord.Colour.orange())

        
@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id in prison_inmates:
        return

    if payload.user_id == client.user.id:
        return

    if payload.guild_id == EX_SERVER and payload.channel_id == EX_WELCOME_CHANNEL:
        if payload.emoji.name in roles:
            member = client.get_guild(payload.guild_id).get_member(payload.user_id)
            await role_handler(member, payload.emoji.name, add=True)
    else:
        await handle_vote_reaction(payload, reaction_added=True)


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id in prison_inmates:
        return

    if payload.user_id == client.user.id:
        return

    if payload.guild_id == EX_SERVER and payload.channel_id == EX_WELCOME_CHANNEL:
        if payload.emoji.name in roles:
            member = client.get_guild(payload.guild_id).get_member(payload.user_id)
            await role_handler(member, payload.emoji.name, add=False)
    else:
        await handle_vote_reaction(payload, reaction_added=False)


async def handle_vote_reaction(payload: discord.RawReactionActionEvent, reaction_added: bool):
    if payload.message_id in ongoing_votes:
        user = client.get_user(payload.user_id)
        channel = client.get_guild(payload.guild_id).get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # prevent triggering the vote system for all emoji not used from the bot
        for reaction in message.reactions:
            if reaction.me and reaction.emoji == payload.emoji.name:
                reaction_used = reaction
                break
        else:
            return

        await ongoing_votes[payload.message_id].store_vote(Vote(user, reaction_used, added=reaction_added))


async def handle_commands(message: discord.Message):
    is_guild = isinstance(message.channel, discord.abc.GuildChannel)
    if message.author.id == client.user.id:  # own bot
        return

    if message.author.id in prison_inmates:
        return

    if is_guild and message.guild.id == EX_SERVER:
        if message.channel.id == EX_WELCOME_CHANNEL:
            await delete_user_message(message)  # no return here

    # prevent forwarding '>>' messages
    if not message.content.startswith(">>") or len(message.content) == 2:  # prevent forwarding '>>' messages
        return

    arg_string = message.clean_content[2:]
    if not is_guild and arg_string.split(" ")[0] not in ["getnative", "grain", "help"]:
        return await message.author.send("This command is not allowed in private chat, sorry.")

    if is_guild:
        today = datetime.datetime.today().strftime("%a %d %b %H:%M:%S")
        logging.info(f"Date: {today} User: {message.author} Server: {message.guild.name} "
                     f"Channel: {message.channel.name} Command: {message.content[:50]}")

    try:
        arg_string = shlex.split(arg_string)
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
        # start the prison release task
        loop.create_task(check_and_release(client))
        logging.info("Start discord run")
        try:
            # bot-Bot
            client.run(config.MAIN.login_token)
            # Test-Bot
            # client.run(config.MAIN.test_token)
        except aiohttp.ClientConnectorError:
            continue
        except KeyboardInterrupt:
            return
        except (InterruptedError, Exception):
            logging.exception("done")
            return

        return


if __name__ == "__main__":
    main()
