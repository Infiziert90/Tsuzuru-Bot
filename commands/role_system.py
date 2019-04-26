import json
import asyncio
from utils import get_role_by_id
from handle_messages import private_msg, delete_user_message
from cmd_manager.filters import is_ex_server
from cmd_manager.decorators import register_command, add_argument

with open("./config/role-settings.json") as f:
    settings = json.load(f)

role_list = list(settings["group"].keys())


async def add_role(client, message, input_role):
    ger_eng = [settings["group"]["ger"], settings["group"]["eng"]]
    for role in message.author.roles:
        if role.id in ger_eng:
            guild_role = get_role_by_id(message.guild, settings['group'][input_role])
            await message.author.add_roles(guild_role)
            await private_msg(message, "Thanks for telling me that!")


async def remove_role(client, message, input_role):
    guild_role = get_role_by_id(message.guild, settings['group'][input_role])
    await message.author.remove_roles(guild_role)
    await private_msg(message, "Role removed.")


@register_command('ger', is_enabled=is_ex_server, description='Self-assign the Ger role.')
async def ger(client, message, args):
    role_ger = get_role_by_id(message.guild, settings['group']['ger'])
    role_eng = get_role_by_id(message.guild, settings['group']['eng'])
    await message.author.add_roles(role_ger)
    await asyncio.sleep(5)
    await message.author.remove_roles(role_eng)
    await private_msg(message, "Danke!")
    await delete_user_message(message)


@register_command('eng', is_enabled=is_ex_server, description='Self-assign the Eng role.')
async def eng(client, message, args):
    role_ger = get_role_by_id(message.guild, settings['group']['ger'])
    role_eng = get_role_by_id(message.guild, settings['group']['eng'])
    await message.author.add_roles(role_eng)
    await asyncio.sleep(5)
    await message.author.remove_roles(role_ger)
    await private_msg(message, "Thanks for telling me that!")
    await delete_user_message(message)


@register_command('role', is_enabled=is_ex_server, description='Add or remove a role.')
@add_argument("role", choices=role_list, help="Name of the role to add.")
@add_argument("--remove", action="store_true", help="Remove the role")
async def role_add_remove(client, message, args):
    await delete_user_message(message)
    if not args.remove:
        await add_role(client, message, args.role)
    else:
        await remove_role(client, message, args.role)
