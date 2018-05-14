import aiohttp
import discord
import asyncio
import random
from handle_messages import private_msg_user


prison_inmates = {}
user_cooldown = set()


def get_role_by_id(server, role_id):
    for role in server.roles:
        if role.id == role_id:
            return role
    return None


def has_role(user, role_id):
    return get_role_by_id(user, role_id) is not None


async def get_file(url, path, filename):
    with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                return None
            with open(f"{path}/{filename}", 'wb') as f:
                f.write(await resp.read())
            return f"{path}/{filename}"


async def delete_role(user, role):
    while prison_inmates[user.id] > 0:
        await asyncio.sleep(60)
        prison_inmates[user.id] -= 1

    prison_inmates.pop(user.id)
    try:
        await user.remove_roles(role)
    except (discord.Forbidden, discord.HTTPException):
        return


async def punish_user(client, message, user=None, reason="Stop using this command!", prison_length=None):
    if isinstance(message.channel, discord.abc.PrivateChannel):
        return

    if message.author.id in prison_inmates:
        return await message.channel.send(f"User in prison can't use this command!")

    if prison_length is None:
        prison_length = random.randint(30, 230)

    user = user or message.author
    if user.id in prison_inmates:
        if prison_length == 0:
            prison_inmates[user.id] = 0
        else:
            prison_inmates[user.id] += prison_length
        return await private_msg_user(message, f"New Time: {prison_inmates[user.id]}min\nReason: {reason}", user)
    else:
        prison_inmates[user.id] = prison_length

    if has_role(user, 221920178940805120):
        role = get_role_by_id(message.guild, 385475870770331650)
    else:
        role = get_role_by_id(message.guild, 385478966955343873)

    await user.add_roles(role)
    asyncio.ensure_future(delete_role(user, role))
    await private_msg_user(message, f"Prison is now active\n Time: {prison_inmates[user.id]}min\nReason: {reason}", user)


def set_user_cooldown(author, time):
    user_cooldown.add(author)
    asyncio.get_event_loop().call_later(time, lambda: user_cooldown.discard(author))
