import aiohttp
import discord
import asyncio
import random
import logging
import datetime
from config.globals import EX_SERVER
from handle_messages import private_msg_user, delete_user_message


# Exception that you can catch, without the risk other errors not getting through
class HelperException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


prison_inmates = {}
user_cooldown = set()


def get_role_by_id(server, role_id):
    for role in server.roles:
        if role.id == role_id:
            return role
    return None


def has_role(user, role_id):
    return get_role_by_id(user, role_id) is not None


async def get_file(url, path, filename, message=None):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                return None
            if message is not None:
                await delete_user_message(message)
            with open(f"{path}/{filename}", 'wb') as f:
                f.write(await resp.read())
            return f"{path}/{filename}"


async def check_and_release(client):
    while True:
        try:
            await asyncio.sleep(60)

            for user_id, prison_array in prison_inmates.copy().items():
                if datetime.datetime.utcnow() >= prison_array[0]:
                    prison_inmates.pop(user_id)
                    guild = client.get_guild(EX_SERVER)
                    member = guild.get_member(user_id)
                    prison_role = get_role_by_id(guild, 451076667377582110)
                    try:
                        await member.remove_roles(prison_role)
                    except (discord.Forbidden, discord.HTTPException):
                        return logging.error("Can't remove user roles")

                    try:
                        await member.edit(roles=[get_role_by_id(guild, role_id) for role_id in prison_array[1]])
                    except (discord.Forbidden, discord.HTTPException):
                        return logging.error("Can't add user roles")
                    except KeyError:
                        return logging.error(f"KeyError for member: {member}")
        except asyncio.CancelledError:
            logging.info("Stopping task")
            return
        except Exception as err:
            logging.error(f"Something in check_and_release went horrible wrong: {err}")


async def punish_user(client, message, user=None, reason="Stop using this command!", prison_length=None):
    if message.author.id in prison_inmates:
        return await message.channel.send(f"User in prison can't use this command!")

    if prison_length is None:
        prison_length = random.randint(30, 230)

    timestamp = datetime.datetime.utcnow()
    prison_time = timestamp + datetime.timedelta(minutes=prison_length)
    user = user or message.author
    if user.id in prison_inmates:
        if prison_length == 0:
            prison_inmates[user.id][0] = timestamp
        else:
            prison_inmates[user.id][0] += datetime.timedelta(minutes=prison_length)
    else:
        prison_inmates[user.id] = [prison_time]
        prison_inmates[user.id].append([role.id for role in user.roles[1:]])
        await user.edit(roles=[role for role in user.roles[1:] if role.managed], reason="Ultimate Prison")
        prison_role = get_role_by_id(message.guild, 451076667377582110)
        await user.add_roles(prison_role)

    prison_time_str = prison_inmates[user.id][0].strftime('%H:%M %a-%b')
    server_time_str = timestamp.strftime('%H:%M %a-%b')
    await send_mod_channel_message(
           client,
           f"Username: {user.name}"
           f"\nNew Time: {prison_length}min"
           f"\nUntil: {prison_time_str if prison_length > 0 else 'Reset'}"
           f"\nReason: {reason}"
           f"\nBy: {message.author.name}"
           f"\n\nServer Time: {server_time_str}"
       )
    await private_msg_user(
           message,
           f"{'Prison is now active' if prison_time == prison_inmates[user.id][0] else 'New release time:'}"
           f"\nUntil: {prison_time_str}"
           f"\nReason: {reason}"
           f"\n\nServer Time: {server_time_str}",
           user
    )


async def send_mod_channel_message(client, message):
    channel = client.get_channel(246368272327507979)
    await channel.send(message)


def set_user_cooldown(author, time):
    user_cooldown.add(author)
    asyncio.get_event_loop().call_later(time, lambda: user_cooldown.discard(author))
