import asyncio
from handle_messages import private_msg


def is_private_chat(message):
    return message.server is None


def is_ex_bot_channel(message):
    if message.channel.id == "300947822956773376":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#public_bot`"))


def is_ex_server(message):
    if message.server and message.server.id == "221919789017202688":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of EX-Server"))


def ex_feature_allowed(message):
    if message.server and message.server.id == "221919789017202688":
        return is_ex_bot_channel(message)
    return True


def is_ex_yuri_channel(message):
    if message.channel.id == "328616388233265154":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yuri`"))


def is_ex_yaoi_channel(message):
    if message.channel.id == "328942447784624128":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-yaoi`"))


def is_ex_trap_channel(message):
    if message.channel.id == "356169435360264192":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#nsfw-traps`"))


def is_ex_fan_release_channel(message):
    if message.channel.id == "221920731871707136":
        return True
    asyncio.ensure_future(private_msg(message, "Stop using this command outside of `#releases_fansubs`"))


def command_not_allowed(message):
    asyncio.ensure_future(private_msg(message, "This command is atm not allowed. Ask Infi for more information."))
    return False

