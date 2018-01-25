#!/usr/bin/python

import shlex
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
from handle_messages import private_msg_code, delete_user_message, message_init

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

client = discord.Client()
commands.load_commands()


@client.event
async def on_ready():
    logging.info(f'Logged in as\nUsername: {client.user.name}\nID: {client.user.id}\nAPI Version: {discord.__version__}')
    gameplayed = discord.Game(name=config.MAIN.get("gameplayed", "Yuri is Love!"))
    await client.change_presence(game=gameplayed)


@client.event
async def on_message(message):
    for role in message.role_mentions:
        if role.id == "239175340180635649":  # ex support role
            return

    if message.server is not None:
        server_id = message.server.id
        server_name = message.server.name
    else:
        server_id = "0"
        server_name = "Private Message"

    if server_id == "221919789017202688":  # eX Server
        if message.channel.id == "338273467483029515":  # welcome
            if message.author.id != client.user.id:  # own bot
                await delete_user_message(message)

    if not message.content.startswith(">>"):
        return

    if message.content.startswith(">>"):
        today = datetime.datetime.today().strftime("%a %d %b %H:%M:%S")
        logging.info(f"Date: {today} User: {message.author} Server: {server_name} Channel: {message.channel.name} "
                     f"Command: {message.content[:50]}")

    arg_string = message.content[2:].split("\n", 1)[0]
    arg_string = shlex.split(arg_string)
    try:
        args = parser.parse_args(arg_string)
    except HelpException as err:
        await delete_user_message(message)
        return await private_msg_code(message, str(err))
    except (UnkownCommandException, argparse.ArgumentError) as err:
        if arg_string[0] in dispatcher.commands:
            await delete_user_message(message)
            return await private_msg_code(message, str(err))
        return

    return await dispatcher.handle(args.command, client, message, args)


@client.event
async def on_message_edit(_, message):
    for role in message.role_mentions:
        if role.id == "239175340180635649":  # ex support role
            return

    if not message.content.startswith(">>"):
        return

    arg_string = message.content[2:].split("\n", 1)[0]
    arg_string = shlex.split(arg_string)
    try:
        args = parser.parse_args(arg_string)
    except HelpException as err:
        await delete_user_message(message)
        return await private_msg_code(message, str(err))
    except (UnkownCommandException, argparse.ArgumentError) as err:
        if arg_string[0] in dispatcher.commands:
            await delete_user_message(message)
            return await private_msg_code(message, str(err))
        return

    return await dispatcher.handle(args.command, client, message, args)


@client.event
async def on_member_join(mem):
    if mem.server.id == "221919789017202688":
        channel = client.get_channel("338273467483029515")
        mention = await client.send_message(channel, f"<@!{mem.id}>")
        em = discord.Embed(description=help_text["bot_bot"]["member_join"], color=333333)
        member_message = await client.send_message(channel, embed=em)
        await client.wait_for_message(channel=channel, author=mem, timeout=300)
        await delete_user_message(member_message)
        await delete_user_message(mention)


def main():
    logging.info("Start discord run")
    message_init(client)
    # bot-Bot
    client.run(config.MAIN.login_token)
    # Test-Bot
    # client.run(config.MAIN.test_token)


if __name__ == "__main__":
    main()
