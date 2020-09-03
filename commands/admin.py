import discord
from config import help_text
from config.globals import *
from .role_system import emotes
from handle_messages import delete_user_message
from cmd_manager.filters import has_admin_permission
from utils import get_file, punish_user, prison_inmates
from cmd_manager.decorators import register_command, add_argument


@register_command(is_admin=has_admin_permission, description='Useless function.')
@add_argument('channel', type=int, help='Target channel id')
@add_argument('text', help='Message text')
async def send_message(client, message, args):
    channel = client.get_channel(args.channel)
    await channel.send(embed=discord.Embed(description=args.text, color=333333))
    await delete_user_message(message)


@register_command(is_admin=has_admin_permission, description='Assign prison.')
@add_argument('--user', '-u', help='Name or id of the user')
@add_argument('--reason', '-r', help='Reason for prison')
@add_argument('--time', '-t', dest="prison_length", type=int, default=30, help='Length for prison [in minutes][0=Reset]')
@add_argument('--no_cet_output', '-utc', dest="cet", action="store_false", default=True, help='Changes the output from CET to UTC')
async def prison(client, message, args):
    await delete_user_message(message)
    if message.author.id in prison_inmates:
        return await message.channel.send(f"Users in prison can't use this command!")
    elif len(args.user) == 0:
        return await message.channel.send(f"Empty username is not allowed!")

    server = client.get_guild(EX_SERVER)
    try:
        user = server.get_member_named(args.user.replace("@", "")) or server.get_member(int(args.user))
    except ValueError:
        return await message.channel.send("User not found, probably the #XXXX identifier was not provided.")
    if not user:
        return await message.channel.send("User not found!")

    await punish_user(client, message, user=user, reason=args.reason, prison_length=args.prison_length, cet_output=args.cet)

    infi = client.get_user(BOT_AUTHOR)
    await infi.send(
        f"Username: {user.name}\n"
        f"New Time: {args.prison_length}min\n"
        f"Full Time: {prison_inmates[user.id][0].strftime('%H:%M %a %d %b') if args.prison_length > 0 else 'Reset'}\n"
        f"Reason: {args.reason}\nBy: {message.author.name}"
    )


@register_command(is_admin=has_admin_permission, description='Purge channel messages.')
@add_argument('channel_id', type=int, help='Channel id')
@add_argument('--reason', '-r', default='bullshit', help='Reason for the purge')
@add_argument('--number', '-n', dest="number", type=int, default=10, help='Number of messages that will be deleted')
async def purge_channel(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(args.channel_id)
    await channel.purge(limit=args.number)
    await message.channel.send(f"Channel: {channel.name}\nNumber: {args.number}\nReason: {args.reason}\n"
                               f"By: {message.author.name}")


@register_command(is_admin=has_admin_permission, description='Send welcome messages.')
async def send_welcome(client, message, args):
    await delete_user_message(message)
    channel = client.get_channel(EX_WELCOME_CHANNEL)
    for key, val in help_text("bot_admin", "welcome_set").items():
        if key == "warning":
            await channel.send(content=val)
        else:
            mes = await channel.send(embed=discord.Embed(description=val, color=333333))
            if key == "command_overview":
                for emoji in emotes.keys():
                    await mes.add_reaction(emoji)


@register_command(is_admin=has_admin_permission, description='Send rules.')
async def send_rules(client, message, args):
    await delete_user_message(message)
    for key, val in help_text("bot_admin", "rule_set").items():
        is_ger = True if key == "ger_ruleset" else False
        channel = client.get_channel(EX_GER_RULE_CHANNEL) if is_ger else client.get_channel(EX_ENG_RULE_CHANNEL)

        embed = discord.Embed(description=val["description"], color=discord.Color.red())
        for idx, rule in enumerate(val["rules"].values()):
            embed.add_field(name=f"{'Regel' if is_ger else 'Rule'} {idx + 1}", value=rule, inline=False)
        embed.add_field(name=f"{'Abschluss' if is_ger else 'End'}", value=val["end"], inline=False)
        await channel.send(embed=embed)

        try:
            for name, text in val["supplement"].items():
                embed = discord.Embed(title=name, description=text, color=discord.Color.red())
                await channel.send(embed=embed)
        except AttributeError:
            pass


@register_command(is_admin=has_admin_permission, description='Sends the newest help yaml.')
async def send_yaml(client, message, args):
    await delete_user_message(message)
    await message.channel.send(file=discord.File("config/text_storage.yaml"))


@register_command(is_admin=has_admin_permission, description='Replace the help yaml.')
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


@register_command(is_admin=has_admin_permission, description='Send internal stats.')
async def output_internals(client, message, args):
    embed = discord.Embed(description="Internal Stats", color=333333)
    embed.add_field(name="Users in prison", value=prison_inmates)
    await message.channel.send(embed=embed)


@register_command('__lolz', is_admin=has_admin_permission, description='Useless function.')
@add_argument('server_id', type=int, help='Server id')
async def lolz(client, message, args):
    server = client.get_guild(args.server_id)
    roles = repr(tuple((role.name, role.id) for role in server.roles)).replace("@everyone", "everyone")
    roles = [roles[i:i+1900] for i in range(0, len(roles), 1900)]
    for x in roles:
        await message.channel.send(x)


@register_command('admin_test', is_admin=has_admin_permission, description='Test admin function.')
async def admin_test(client, message, args):
    await message.channel.send("Noob!")
