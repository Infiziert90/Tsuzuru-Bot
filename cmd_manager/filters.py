import asyncio
import random

from utils import punish_user
from handle_messages import private_msg, delete_user_message


def is_private_chat(message):
    return message.server is None


def is_ex_bot_channel(message):
    if message.channel.id == "300947822956773376":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#public_bot`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_server(message):
    if message.server and message.server.id == "221919789017202688":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of EX-Server"))
    asyncio.ensure_future(delete_user_message(message))


def ex_feature_allowed(message):
    if message.server and message.server.id == "221919789017202688":
        return is_ex_bot_channel(message)
    return True


def is_ex_yuri_channel(message):
    if message.channel.id == "328616388233265154":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yuri`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_yaoi_channel(message):
    if message.channel.id == "328942447784624128":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yaoi`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_trap_channel(message):
    if message.channel.id == "356169435360264192":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-traps`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_fan_release_channel(message):
    if message.channel.id == "221920731871707136":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#releases_fansubs`"))
    asyncio.ensure_future(delete_user_message(message))


def command_not_allowed(message):
    asyncio.ensure_future(private_msg(message, "This command is atm not allowed. Ask Infi for more information."))
    asyncio.ensure_future(delete_user_message(message))
    return False


def is_admin_command(client, message):
    if message.channel.id == "246368272327507979":
        return True
    if message.author.id == "134750562062303232":
        return True
    asyncio.ensure_future(punish_user(client, message))
    return False


def is_troll_command(client, message):
    asyncio.ensure_future(delete_user_message(message))
    if message.author.id == "134750562062303232":
        return True
    if random.randint(1, 3) == 2:
        return True
    asyncio.ensure_future(punish_user(client, message))
    return False
