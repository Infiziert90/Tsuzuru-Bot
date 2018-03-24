import random
import discord
import asyncio
from config import help_text
from utils import get_role_by_id, has_role, get_file
from cmd_manager.decorators import register_command, add_argument
from cmd_manager.filters import is_ex_mod_channel
from handle_messages import delete_user_message, private_msg_user


@register_command('x264', description='Post some links for x264')
async def x264(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for x264?", description=help_text("bot_bot", "x264_links"))
    await client.send_message(message.channel, embed=em)


@register_command('avisynth', description='Post some links for Avisynth')
async def avisynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Avisynth?", description=help_text("bot_bot", "avs_links"))
    await client.send_message(message.channel, embed=em)


@register_command('vapoursynth', description='Post some links for Vapoursynth')
async def vapoursynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for Vapoursynth?", description=help_text("bot_bot", "vs_links"))
    await client.send_message(message.channel, embed=em)


@register_command('yuuno', description='Post some links for Yuuno')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Yuuno?", description=help_text("bot_bot", "yuuno_links"))
    await client.send_message(message.channel, embed=em)


@register_command('getn', description='Post some links for getnative')
async def getn(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for getnative?", description=help_text("bot_bot", "getnative_links"))
    await client.send_message(message.channel, embed=em)


@register_command('__lolz', description='Useless function.')
@add_argument('server_id', help='Server where you will check the ids.')
async def lolz(client, message, args):
    server = client.get_server(args.server_id)
    await client.send_message(message.channel, repr(tuple((role.name, role.id) for role in server.roles)))


@register_command('send_message', is_enabled=is_ex_mod_channel, description='Useless function.')
@add_argument('channel', help='Channel where the message will be posted.')
@add_argument('--yaml-name', '-yn', dest='name', help='Name from your .yaml text')
@add_argument('--text', '-t', dest='text', help='Message text')
async def send_message(client, message, args):
    if message.channel.is_private:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    channel = client.get_channel(args.channel)
    if args.name:
        em = discord.Embed(description=help_text("bot_bot", args.name), color=333333)
    elif args.text:
        em = discord.Embed(description=args.text, color=333333)
    else:
        return

    await client.send_message(channel, embed=em)
    await delete_user_message(message)


@register_command('prison', description='Assign prison.')
@add_argument('--user', '-u', help='UserID from the user.')
@add_argument('--reason', '-r', help='Reason for prison.')
@add_argument('--time', '-t', dest="prison_length", type=int, default=30, help='Lenght for the prison in minutes.')
async def prison(client, message, args):
    await delete_user_message(message)
    if message.channel.is_private or message.author.id in prison_inmates:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    if args.prison_length > 180:
        return await client.send_message(message.channel, f"Prison lenght max. is 180min")

    server = client.get_server("221919789017202688")
    user = server.get_member_named(args.user) or server.get_member(args.user)
    if not user:
        return await client.send_message(message.channel, "User not found.")

    await punish_user(message, client, user=user, reason=args.reason, prison_length=args.prison_length)
    await client.send_message(message.channel, f"Username: {user.name}\nTime: {args.prison_length}min\nReason: {args.reason}\nBy: {message.author.name}")


@register_command('purge_channel', description='Purge channel messages.')
@add_argument('channel_id', help='UserID from the user.')
@add_argument('--reason', '-r', default='bullshit', help='Reason for the purge.')
@add_argument('--number', '-n', dest="number", type=int, default=10, help='Number of messages that will be deleted.')
async def purge_channel(client, message, args):
    if message.channel.is_private:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    await delete_user_message(message)
    channel = client.get_channel(args.channel_id)
    await client.purge_from(channel, limit=args.number)
    await client.send_message(message.channel, f"Channel: {channel.name}\nNumber: {args.number}\nReason: {args.reason}\nBy: {message.author.name}")


@register_command('send_welcome', description='Purge #welcome and resend messages.')
async def send_welcome(client, message, args):
    if message.channel.is_private:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    await delete_user_message(message)
    channel = client.get_channel("338273467483029515")
    await client.purge_from(channel, limit=100)
    em = discord.Embed(description=help_text("bot_bot", "command_overview"), color=333333)
    em1 = discord.Embed(description=help_text("bot_bot", "help_message"), color=333333)
    em2 = discord.Embed(description=help_text("bot_bot", "member_join"), color=333333)
    await client.send_message(channel, embed=em)
    await client.send_message(channel, embed=em1)
    await client.send_message(channel, embed=em2)


@register_command('send_yaml', description='Sends the newest help yaml.')
async def send_yaml(client, message, args):
    if message.channel.is_private:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    await delete_user_message(message)
    await client.send_file(message.channel, "config/text_storage.yaml")


@register_command('replace_yaml', description='Sends the newest help yaml.')
async def replace_yaml(client, message, args):
    if message.channel.is_private:
        return

    if message.channel.id != "246368272327507979":
        return await punish_user(message, client)

    url = message.attachments[0]["url"]
    success = await get_file(url, "config", "text_storage.yaml")
    if success:
        await client.send_message(message.channel, "Replaced file.")
    else:
        await client.send_message(message.channel, "Failed for unknown reasons.")


prison_inmates = []
async def delete_role(client, prison_length, user, role):
    await asyncio.sleep(prison_length * 60)
    try:
        await client.remove_roles(user, role)
    except (discord.Forbidden, discord.HTTPException):
        pass
    prison_inmates.remove(user.id)


async def punish_user(message, client, user=None, reason="Stop using this command!", prison_length=random.randint(30, 230)):
    user = user or message.author
    prison_inmates.append(user.id)
    if has_role(user, "221920178940805120"):
        role = get_role_by_id(message.channel.server, "385475870770331650")
    else:
        role = get_role_by_id(message.channel.server, "385478966955343873")

    await client.add_roles(user, role)
    asyncio.ensure_future(delete_role(client, prison_length, user, role))
    await private_msg_user(message, f"Prison is now active\n Time: {prison_length}min\nReason: {reason}", user)

