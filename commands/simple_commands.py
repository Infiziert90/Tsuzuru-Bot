import discord
from config import help_text
from cmd_manager.bot_args import parser
from handle_messages import delete_user_message, private_msg_code
from cmd_manager.decorators import register_command, add_argument


@register_command('help', description='Post the help message.')
async def help_str(client, message, args):
    await delete_user_message(message)
    await private_msg_code(message, parser.format_help())


@register_command('x264', description='Post help links for x264')
async def x264(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for x264?", description=help_text("bot_bot", "x264_links"))
    await message.channel.send(embed=em)


@register_command('avi', description='Post help links for Avisynth')
async def avisynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Avisynth?", description=help_text("bot_bot", "avs_links"))
    await message.channel.send(embed=em)


@register_command('vs', description='Post help links for VapourSynth')
async def vapoursynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for VapourSynth?", description=help_text("bot_bot", "vs_links"))
    await message.channel.send(embed=em)


@register_command('yuuno', description='Post help links for Yuuno')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Yuuno?", description=help_text("bot_bot", "yuuno_links"))
    await message.channel.send(embed=em)


@register_command('ffmpeg', description='Post help links for ffmpeg')
async def ffmpeg(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="ffmpeg?", description=help_text("bot_bot", "ffmpeg_links"))
    await message.channel.send(embed=em)


@register_command('getn', description='Post help links for getnative')
async def getn(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for getnative?", description=help_text("bot_bot", "getnative_links"))
    await message.channel.send(embed=em)


@register_command('__lolz', description='Useless function.')
@add_argument('server_id', type=int, help='Server id')
async def lolz(client, message, args):
    server = client.get_guild(args.server_id)
    roles = repr(tuple((role.name, role.id) for role in server.roles)).replace("@everyone", "everyone")
    roles = [roles[i:i+1900] for i in range(0, len(roles), 1900)]
    for x in roles:
        await message.channel.send(x)
