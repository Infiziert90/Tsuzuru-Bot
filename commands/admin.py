import discord
from config import help_text
from cmd_manager.filters import is_admin_command
from utils import get_file, punish_user, prison_inmates
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command, add_argument


@register_command('send_message', is_admin=is_admin_command, description='Useless function.')
@add_argument('channel', help='Channel where the message will be posted.')
@add_argument('text', help='Message text')
async def send_message(client, message, args):
    channel = client.get_channel(args.channel)
    em = discord.Embed(description=args.text, color=333333)

    await client.send_message(channel, embed=em)
    await delete_user_message(message)


@register_command('prison', is_admin=is_admin_command, description='Assign prison.')
@add_argument('--user', '-u', help='UserID from the user.')
@add_argument('--reason', '-r', help='Reason for prison.')
@add_argument('--time', '-t', dest="prison_length", type=int, default=30, help='Lenght for the prison in minutes.')
async def prison(client, message, args):
    await delete_user_message(message)
    if message.author.id in prison_inmates:
        return

    if args.prison_length > 180:
        return await client.send_message(message.channel, f"Prison lenght max. is 180min")

    server = client.get_server("221919789017202688")
    user = server.get_member_named(args.user) or server.get_member(args.user)
    if not user:
        return await client.send_message(message.channel, "User not found.")

    await punish_user(client, message, user=user, reason=args.reason, prison_length=args.prison_length)
    await client.send_message(message.channel, f"Username: {user.name}\nTime: {args.prison_length}min\nReason: {args.reason}\nBy: {message.author.name}")


@register_command('purge_channel', is_admin=is_admin_command, description='Purge channel messages.')
@add_argument('channel_id', help='UserID from the user.')
@add_argument('--reason', '-r', default='bullshit', help='Reason for the purge.')
@add_argument('--number', '-n', dest="number", type=int, default=10, help='Number of messages that will be deleted.')
async def purge_channel(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(args.channel_id)
    await client.purge_from(channel, limit=args.number)
    await client.send_message(message.channel, f"Channel: {channel.name}\nNumber: {args.number}\nReason: {args.reason}\nBy: {message.author.name}")


@register_command('send_welcome', is_admin=is_admin_command, description='Purge #welcome and resend messages.')
async def send_welcome(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel("338273467483029515")
    await client.purge_from(channel, limit=100)
    em = discord.Embed(description=help_text("bot_bot", "command_overview"), color=333333)
    em1 = discord.Embed(description=help_text("bot_bot", "help_message"), color=333333)
    em2 = discord.Embed(description=help_text("bot_bot", "member_join"), color=333333)
    await client.send_message(channel, embed=em)
    await client.send_message(channel, embed=em1)
    await client.send_message(channel, embed=em2)


@register_command('send_yaml', is_admin=is_admin_command, description='Sends the newest help yaml.')
async def send_yaml(client, message, args):
    await delete_user_message(message)
    await client.send_file(message.channel, "config/text_storage.yaml")


@register_command('replace_yaml', is_admin=is_admin_command, description='Sends the newest help yaml.')
async def replace_yaml(client, message, args):
    url = message.attachments[0]["url"]
    success = await get_file(url, "config", "text_storage.yaml")
    if success:
        await client.send_message(message.channel, "Replaced file.")
    else:
        await client.send_message(message.channel, "Failed for unknown reasons.")
