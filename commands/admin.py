import discord
from config import help_text
from cmd_manager.filters import EX_SERVER, EX_WELCOME_CHANNEL, is_admin_command
from utils import get_file, punish_user, prison_inmates, user_roles
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command, add_argument
from .role_system import roles


@register_command('send_message', is_admin=is_admin_command, description='Useless function.')
@add_argument('channel', type=int, help='Target channel id')
@add_argument('text', help='Message text')
async def send_message(client, message, args):
    channel = client.get_channel(args.channel)
    await channel.send(embed=discord.Embed(description=args.text, color=333333))
    await delete_user_message(message)


@register_command('prison', is_admin=is_admin_command, description='Assign prison.')
@add_argument('--user', '-u', help='Name or id from the user')
@add_argument('--reason', '-r', help='Reason for prison')
@add_argument('--time', '-t', dest="prison_length", type=int, default=30, help='Length for the prison [in min][0 = reset]')
async def prison(client, message, args):
    await delete_user_message(message)
    if message.author.id in prison_inmates or message.author.id in user_roles:
        return await message.channel.send(f"User in prison can't use this command!")
    elif len(args.user) == 0:
        return await message.channel.send(f"Empty username is not allowed!")

    server = client.get_guild(EX_SERVER)
    user = server.get_member_named(args.user.replace("@", "")) or server.get_member(int(args.user))
    if not user:
        return await message.channel.send("User not found!")

    await punish_user(client, message, user=user, reason=args.reason, prison_length=args.prison_length)

    infi = client.get_user(134750562062303232)
    await infi.send(f"Username: {user.name}\nNew Time: {args.prison_length}min\nFull Time: "
                    f"{str(prison_inmates[user.id]) + 'min' if args.prison_length > 0 else 'Reset'}\nReason: "
                    f"{args.reason}\nBy: {message.author.name}")


@register_command('purge_channel', is_admin=is_admin_command, description='Purge channel messages.')
@add_argument('channel_id', type=int, help='Channel id')
@add_argument('--reason', '-r', default='bullshit', help='Reason for the purge')
@add_argument('--number', '-n', dest="number", type=int, default=10, help='Number of messages that will be deleted')
async def purge_channel(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(args.channel_id)
    await channel.purge(limit=args.number)
    await message.channel.send(f"Channel: {channel.name}\nNumber: {args.number}\nReason: {args.reason}\n"
                               f"By: {message.author.name}")


@register_command('send_welcome', is_admin=is_admin_command, description='Send welcome messages.')
async def send_welcome(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(EX_WELCOME_CHANNEL)
    await channel.send(content=help_text("bot_bot", "welcome_note"))
    mes = await channel.send(embed=discord.Embed(description=help_text("bot_bot", "command_overview"), color=333333))
    for emoji in roles.keys():
        await mes.add_reaction(emoji)
    await channel.send(embed=discord.Embed(description=help_text("bot_bot", "help_message"), color=333333))
    await channel.send(embed=discord.Embed(description=help_text("bot_bot", "member_join"), color=333333))


@register_command('send_yaml', is_admin=is_admin_command, description='Sends the newest help yaml.')
async def send_yaml(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File("config/text_storage.yaml"))


@register_command('replace_yaml', is_admin=is_admin_command, description='Replace the help yaml.')
async def replace_yaml(client, message, args):
    try:
        url = message.attachments[0].url
    except IndexError:
        return await message.channel.send("Need file as attachment!")

    success = await get_file(url, "config", "text_storage.yaml")
    if success:
        await message.channel.send("Replaced file.")
    else:
        await message.channel.send("Failed for unknown reasons.")


@register_command('output_internals', is_admin=is_admin_command, description='Send internal stats')
async def replace_yaml(client, message, args):
    embed = discord.Embed(description="Internal Stats", color=333333)
    embed.add_field(name="User in prison", value=prison_inmates)
    embed.add_field(name="Saved roles for user", value=user_roles)
    await message.channel.send(embed=embed)
