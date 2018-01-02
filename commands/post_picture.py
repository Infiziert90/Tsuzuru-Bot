import os
import discord
from config import config
from handle_messages import delete_user_message
from cmd_manager.filters import is_ex_yuri_channel, is_ex_yaoi_channel, is_ex_trap_channel, command_not_allowed
from cmd_manager.decorators import register_command

yuri_folder = config.PICTURE.yuri
yaoi_folder = config.PICTURE.yaoi
trap_folder = config.PICTURE.trap
spam_folder = config.PICTURE.spam


async def send_picture(client, folder, channel_id):
    for i in os.listdir(folder):
        channel = client.get_channel(channel_id)
        try:
            await client.send_file(channel, folder + i)
            os.remove(folder + i)
            return
        except discord.HTTPException:
            os.remove(folder + i)
            print("Error: File to large")


@register_command('yuri', is_enabled=is_ex_yuri_channel, description='Post a yuri picture.')
async def yuri(client, message, args):
    await delete_user_message(message)
    await send_picture(client, yuri_folder, "328616388233265154")


@register_command('trap', is_enabled=is_ex_trap_channel, description='Post a trap picture.')
async def trap(client, message, args):
    await delete_user_message(message)
    await send_picture(client, trap_folder, "356169435360264192")


@register_command('yaoi', is_enabled=is_ex_yaoi_channel, description='Post a yaoi picture.')
async def yaoi(client, message, args):
    await delete_user_message(message)
    await send_picture(client, yaoi_folder, "328942447784624128")


@register_command('miles', is_enabled=command_not_allowed, description='Post the miles picture.')
async def miles(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "miles.jpg", content=f"From: {message.author.display_name}")


@register_command('paid', is_enabled=command_not_allowed, description='Post the getting_paid picture.')
async def paid(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "getting_paid.jpg", content=f"From: {message.author.display_name}")


@register_command('masterrace', description='Arch == Masterrace.')
async def masterrace(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "arch.png", content=f"From: {message.author.display_name}")


@register_command('bestunion', description='sowjet == bestunion.')
async def bestunion(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "sowjet.png", content=f"From: {message.author.display_name}")


@register_command('linux', description='linux == linux.')
async def linux(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "linux.png", content=f"From: {message.author.display_name}")


@register_command('yuriislove', description='yuri == yuri is love.')
async def yuriislove(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "yuri.jpeg", content=f"From: {message.author.display_name}")


@register_command('kevin', description='kevin == kevin')
async def kevin(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, spam_folder + "kevin.jpeg", content=f"From: {message.author.display_name}")
