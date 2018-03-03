import discord
import asyncio
from config import help_text
from utils import get_role_by_id
from cmd_manager.decorators import register_command, add_argument
from cmd_manager.filters import is_ex_mod_channel
from handle_messages import delete_user_message


@register_command('x264', description='Post some links for x264')
async def x264(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for x264?", description=help_text["bot_bot"]["x264_links"])
    await client.send_message(message.channel, embed=em)


@register_command('avisynth', description='Post some links for Avisynth')
async def avisynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Avisynth?", description=help_text["bot_bot"]["avs_links"])
    await client.send_message(message.channel, embed=em)


@register_command('vapoursynth', description='Post some links for Vapoursynth')
async def vapoursynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for Vapoursynth?", description=help_text["bot_bot"]["vs_links"])
    await client.send_message(message.channel, embed=em)


@register_command('yuuno', description='Post some links for Yuuno')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Yuuno?", description=help_text["bot_bot"]["yuuno_links"])
    await client.send_message(message.channel, embed=em)


@register_command('getn', description='Post some links for getnative')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for getnative?", description=help_text["bot_bot"]["getnative_links"])
    await client.send_message(message.channel, embed=em)


@register_command('__lolz', description='Useless function.')
@add_argument('server_id', help='Server where you will check the ids.')
async def lolz(client, message, args):
    server = client.get_server(args.server_id)
    await client.send_message(message.channel, repr(tuple((role.name, role.id) for role in server.roles)))


@register_command('send_message', description='Useless function.')
@add_argument('channel', help='Channel where the message will be posted.')
@add_argument('name', help='Name from your .yaml text')
async def send_message(client, message, args):
    channel = client.get_channel(args.channel)
    em = discord.Embed(description=help_text["bot_bot"][args.name], color=333333)
    await client.send_message(channel, embed=em)
    await delete_user_message(message)


@register_command('prison', is_enabled=is_ex_mod_channel, description='Assign prison.')
@add_argument('user', help='UserID from the user.')
@add_argument('reason', help='Reason for prison.')
@add_argument('--prison-type', '-pt', dest="prison_type", type=int, default=0, help='0 is Ger, 1 is Eng')
@add_argument('--prison-length', '-pl', dest="prison_length", type=int, default=30, help='Lenght for the prison in minutes.')
async def send_message(client, message, args):
    await delete_user_message(message)

    if args.prison_type == 0:
        role = get_role_by_id(message.channel.server, "385475870770331650")
    else:
        role = get_role_by_id(message.channel.server, "385478966955343873")

    if args.prison_length > 180:
        await client.send_message(message.channel, f"Prison lenght max. is 180min")

    server = client.get_server("221919789017202688")
    user = server.get_member_named(args.user)
    if user is None:
        user = server.get_member(args.user)
    if user:
        await client.add_roles(user, role)
        await client.send_message(message.channel, f"Username: {user.name}\nTime: {args.prison_length}min"
                                                   f"\nReason: {args.reason}\nBy: {message.author.name}")
        asyncio.ensure_future(delete_role(client, args, user, role))
        try:
            msg_answer = await client.start_private_message(user)
            await client.send_message(msg_answer, content=f"Prison is now active\n Time: {args.prison_length}min\nReason: {args.reason}")
        except:
            pass
    else:
        await client.send_message(message.channel, "User not found.")


async def delete_role(client, args, user, role):
    await asyncio.sleep(args.prison_length * 60)
    try:
        await client.remove_roles(user, role)
    except (discord.Forbidden, discord.HTTPException):
        pass
