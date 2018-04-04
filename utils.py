import aiohttp
import discord
import asyncio
import random
from handle_messages import private_msg_user


prison_inmates = []
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


async def delete_role(client, prison_length, user, role):
    await asyncio.sleep(prison_length * 60)
    prison_inmates.remove(user.id)
    try:
        await client.remove_roles(user, role)
    except (discord.Forbidden, discord.HTTPException):
        return


async def punish_user(client, message, user=None, reason="Stop using this command!", prison_length=None):
    if message.channel.is_private:
        return

    if message.author.id in prison_inmates:
        return await client.send_message(message.channel, f"User in prison can't use this command!")

    if prison_length is None:
        prison_length = random.randint(30, 230)

    user = user or message.author
    prison_inmates.append(user.id)
    if has_role(user, "221920178940805120"):
        role = get_role_by_id(message.channel.server, "385475870770331650")
    else:
        role = get_role_by_id(message.channel.server, "385478966955343873")

    await client.add_roles(user, role)
    asyncio.ensure_future(delete_role(client, prison_length, user, role))
    await private_msg_user(message, f"Prison is now active\n Time: {prison_length}min\nReason: {reason}", user)


def set_user_cooldown(author, time):
    user_cooldown.add(author)
    asyncio.get_event_loop().call_later(time, lambda: user_cooldown.discard(author))
