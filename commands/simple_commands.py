import random
import discord
from config import help_text
from cmd_manager.bot_args import build_custom_help
from handle_messages import delete_user_message, private_msg_code
from cmd_manager.decorators import register_command, add_argument


@register_command('help', description='Show this help message.')
async def help_str(client, message, args):
    await delete_user_message(message)

    help_string = build_custom_help()
    # TODO split in better positions
    for val in [help_string[i:i + 1900] for i in range(0, len(help_string), 1900)]:
        await private_msg_code(message, val)


NAMES = [
    "Satan", "God", "Myself", "yuri", "GNU/Linux", "a brigher future", "hopelessness",
    "weeabooism",
]


@register_command(description='Select one of the given choices.')
@add_argument('choices', nargs='+')
async def choose(client, message, args):
    choice = random.choice(args.choices)
    name = random.choice(NAMES + [message.author.name])

    await message.channel.send(f"In the name of {name} I choose: {choice}")


@register_command(description='[Link] Helpful links for x264')
async def x264(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for x264?", description=help_text("bot_bot", "x264_links"))
    await message.channel.send(embed=em)


@register_command('avi', description='[Link] Helpful links for Avisynth')
async def avisynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Avisynth?", description=help_text("bot_bot", "avs_links"))
    await message.channel.send(embed=em)


@register_command('vs', description='[Link] Helpful links for VapourSynth')
async def vapoursynth(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for VapourSynth?", description=help_text("bot_bot", "vs_links"))
    await message.channel.send(embed=em)


@register_command(description='[Link] Helpful links for Yuuno')
async def yuuno(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for Yuuno?", description=help_text("bot_bot", "yuuno_links"))
    await message.channel.send(embed=em)


@register_command(description='[Link] Helpful links for ffmpeg')
async def ffmpeg(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="ffmpeg?", description=help_text("bot_bot", "ffmpeg_links"))
    await message.channel.send(embed=em)


@register_command(description='[Link] Helpful links for getnative')
async def getn(client, message, args):
    await delete_user_message(message)
    em = discord.Embed(title="You need help for getnative?", description=help_text("bot_bot", "getnative_links"))
    await message.channel.send(embed=em)
