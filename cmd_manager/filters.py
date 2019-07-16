import asyncio
import random
from utils import punish_user
from handle_messages import private_msg, delete_user_message

EX_SERVER = 221919789017202688
EX_WELCOME_CHANNEL = 338273467483029515
EX_GER_RULE_CHANNEL = 598930909676437504
EX_ENG_RULE_CHANNEL = 598933758258970644
EX_ADMIN_CHANNEL = 246368272327507979
EX_BOT_CHANNEL = 300947822956773376
EX_FANSUB_CHANNEL = 221920731871707136
EX_YURI_CHANNEL = 328616388233265154
EX_YAOI_CHANNEL = 328942447784624128
EX_TRAP_CHANNEL = 328942447784624128


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


def is_ex_yuri_channel(message):
    if message.channel.id == EX_YURI_CHANNEL:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yuri`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_yaoi_channel(message):
    if message.channel.id == EX_YAOI_CHANNEL:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yaoi`"))
    asyncio.ensure_future(delete_user_message(message))


def is_ex_trap_channel(message):
    if message.channel.id == EX_TRAP_CHANNEL:
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-traps`"))
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
