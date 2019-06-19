import os
import random
import discord
import logging
from config import config
from handle_messages import delete_user_message
from cmd_manager.filters import is_ex_yuri_channel, is_ex_yaoi_channel, is_ex_trap_channel, EX_YURI_CHANNEL, \
                                EX_TRAP_CHANNEL, EX_YAOI_CHANNEL
from cmd_manager.decorators import register_command

yuri_folder = config.PICTURE.yuri
yaoi_folder = config.PICTURE.yaoi
trap_folder = config.PICTURE.trap
spam_folder = config.PICTURE.spam


async def send_image(client, folder, channel_id):
    images = os.listdir(folder)
    for _ in images:
        image = folder + images[random.randint(0, len(images))]
        channel = client.get_channel(channel_id)
        try:
            await channel.send(file=discord.File(image))
            os.remove(image)
            return
        except discord.HTTPException:
            os.remove(image)
            logging.info("Error: File to large")


@register_command('yuri', is_enabled=is_ex_yuri_channel, description='Post a yuri image.')
async def yuri(client, message, args):
    await delete_user_message(message)
    await send_image(client, yuri_folder, EX_YURI_CHANNEL)


@register_command('trap', is_enabled=is_ex_trap_channel, description='Post a trap image.')
async def trap(client, message, args):
    await delete_user_message(message)
    await send_image(client, trap_folder, EX_TRAP_CHANNEL)


@register_command('yaoi', is_enabled=is_ex_yaoi_channel, description='Post a yaoi image.')
async def yaoi(client, message, args):
    await delete_user_message(message)
    await send_image(client, yaoi_folder, EX_YAOI_CHANNEL)

# Spam images
@register_command('autism', description='Autism!')
async def autism(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "autism.gif"), content=f"From: {message.author.display_name}")


@register_command('bait', description='Bait (Arch Linux)')
async def bait(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "bait.png"), content=f"From: {message.author.display_name}")


@register_command('bestunion', description='sowjetunion == bestunion.')
async def bestunion(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "sowjet.png"), content=f"From: {message.author.display_name}")


@register_command('capi', description='Capitalism')
async def capi(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "capi.jpg"), content=f"From: {message.author.display_name}")


@register_command('cute', description='Waifu trash')
async def cute(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "cute.gif"), content=f"From: {message.author.display_name}")


@register_command('eyes', description='Waifu trash')
async def eyes(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "eyes.gif"), content=f"From: {message.author.display_name}")


@register_command('jail', description='Jail is over there!')
async def jail(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "jail.gif"), content=f"From: {message.author.display_name}")


@register_command('kage', description='The normal kage')
async def kage(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "kage.png"), content=f"From: {message.author.display_name}")


@register_command('kevin', description='Kevin! Aus!')
async def kevin(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "kevin.jpeg"), content=f"From: {message.author.display_name}")


@register_command('linux', description='Linux.')
async def linux(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "linux.png"), content=f"From: {message.author.display_name}")


@register_command('masterrace', description='Arch == Masterrace.')
async def masterrace(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "arch.png"), content=f"From: {message.author.display_name}")


@register_command('paid', description='Post the getting_paid picture.')
async def paid(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "getting_paid.jpg"), content=f"From: {message.author.display_name}")


@register_command('season2', description='Waifu trash')
async def season2(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "season2.gif"), content=f"From: {message.author.display_name}")


@register_command('trash', description='Anime is trash')
async def trash(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "trash.gif"), content=f"From: {message.author.display_name}")


@register_command('waifu', description='Waifu trash')
async def waifu(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "waifu.gif"), content=f"From: {message.author.display_name}")


@register_command('windows', description='Windows trash')
async def windows(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "windows.jpg"), content=f"From: {message.author.display_name}")


@register_command('yuri_is_love', description='Yuri is love.')
async def yuri_is_love(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File(spam_folder + "yuri.jpeg"), content=f"From: {message.author.display_name}")
