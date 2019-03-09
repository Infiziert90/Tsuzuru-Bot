import discord
from config import help_text
from cmd_manager.filters import is_admin_command
from utils import get_file, punish_user, prison_inmates, user_roles
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command, add_argument


@register_command('send_message', is_admin=is_admin_command, description='Useless function.')
@add_argument('channel', type=int, help='Channel where the message will be posted.')
@add_argument('text', help='Message text')
async def send_message(client, message, args):
    channel = client.get_channel(args.channel)
    em = discord.Embed(description=args.text, color=333333)

    await channel.send(embed=em)
    await delete_user_message(message)


@register_command('prison', is_admin=is_admin_command, description='Assign prison.')
@add_argument('--user', '-u', help='UserID from the user.')
@add_argument('--reason', '-r', help='Reason for prison.')
@add_argument('--time', '-t', dest="prison_length", type=int, default=30, help='Lenght for the prison in minutes. [0 reset]')
async def prison(client, message, args):
    await delete_user_message(message)
    if message.author.id in prison_inmates:
        return await message.channel.send(f"User in prison can't use this command!")
    if message.author.id in user_roles:
        return await message.channel.send(f"User in prison can't use this command!")
    elif len(args.user) == 0:
        return await message.channel.send(f"Empty username is not allowed.")

    server = client.get_guild(221919789017202688)
    user = server.get_member_named(args.user) or server.get_member(args.user)
    if not user:
        return await message.channel.send("User not found.")

    await punish_user(client, message, user=user, reason=args.reason, prison_length=args.prison_length)

    infi = client.get_user(134750562062303232)
    await infi.send(f"Username: {user.name}\nNew Time: {args.prison_length}min\nFull Time: "
                    f"{prison_inmates[user.id] if args.prison_length > 0 else 'Reset'}\nReason: "
                    f"{args.reason}\nBy: {message.author.name}")


@register_command('purge_channel', is_admin=is_admin_command, description='Purge channel messages.')
@add_argument('channel_id', type=int, help='UserID from the user.')
@add_argument('--reason', '-r', default='bullshit', help='Reason for the purge.')
@add_argument('--number', '-n', dest="number", type=int, default=10, help='Number of messages that will be deleted.')
async def purge_channel(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(args.channel_id)
    await channel.purge(limit=args.number)
    await message.channel.send(f"Channel: {channel.name}\nNumber: {args.number}\nReason: {args.reason}\nBy: {message.author.name}")


@register_command('send_welcome', is_admin=is_admin_command, description='Purge #welcome and resend messages.')
async def send_welcome(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(338273467483029515)
    await channel.send(embed=discord.Embed(description=help_text("bot_bot", "command_overview"), color=333333))
    await channel.send(embed=discord.Embed(description=help_text("bot_bot", "help_message"), color=333333))
    await channel.send(embed=discord.Embed(description=help_text("bot_bot", "member_join"), color=333333))


@register_command('send_yaml', is_admin=is_admin_command, description='Sends the newest help yaml.')
async def send_yaml(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File("config/text_storage.yaml"))


@register_command('replace_yaml', is_admin=is_admin_command, description='Sends the newest help yaml.')
async def replace_yaml(client, message, args):
    url = message.attachments[0].url
    success = await get_file(url, "config", "text_storage.yaml")
    if success:
        await message.channel.send("Replaced file.")
    else:
        await message.channel.send("Failed for unknown reasons.")
