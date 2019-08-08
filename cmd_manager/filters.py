import asyncio
import random
from utils import punish_user
from config.globals import *
from handle_messages import private_msg, delete_user_message


def is_ex_bot_channel(message):
    if message.channel.id == EX_BOT_CHANNEL:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#public_bot`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_server(message):
    if message.guild and message.guild.id == EX_SERVER:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of eX-Server"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_fan_release_channel(message):
    if message.channel.id == EX_FANSUB_CHANNEL:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#releases_fansubs`"))
    asyncio.ensure_future(delete_user_message(message))


def command_not_allowed(message):
    asyncio.ensure_future(private_msg(message, "This command is not allowed.\nAsk @Infi#8527 for more information."))
    asyncio.ensure_future(delete_user_message(message))
    return False


def is_admin_command(client, message):
    if message.guild.id == EX_SERVER:
        if message.channel.id == EX_ADMIN_CHANNEL:
            return True
        asyncio.ensure_future(punish_user(client, message))
    return False


def is_troll_command(client, message):
    if message.guild.id == EX_SERVER:
        asyncio.ensure_future(delete_user_message(message))
        if random.randint(1, 3) == 2:
            return True
        asyncio.ensure_future(punish_user(client, message))
    return False
