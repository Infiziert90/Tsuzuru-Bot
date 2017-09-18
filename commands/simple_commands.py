import discord
from config import help_text
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command, add_argument


@register_command('x264', description='Post some links for x264')
async def x264(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for x264?", description=help_text["bot_bot"]["x264_links"])
    await client.send_message(message.channel, embed=em)


@register_command('avisynth', description='Post some links for Avisynth')
async def avisynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for Avisynth?", description=help_text["bot_bot"]["avs_links"])
    await client.send_message(message.channel, embed=em)


@register_command('vapoursynth', description='Post some links for Vapoursynth')
async def vapoursynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for Vapoursynth?", description=help_text["bot_bot"]["vs_links"])
    await client.send_message(message.channel, embed=em)


@register_command('yuuno', description='Post some links for Yuuno')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need Help for Yuuno?", description=help_text["bot_bot"]["yuuno_links"])
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
