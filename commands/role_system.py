import json
import asyncio
from utils import get_role_by_id
from handle_messages import private_msg, delete_user_message
from cmd_manager.filters import is_ex_server
from cmd_manager.decorators import register_command, add_argument

with open("./config/role-settings.json") as f:
    settings = json.load(f)

role_list = list(settings["group"].keys())


async def add_role(client, message, input_group):
    ger_eng = [settings["group"]["ger"], settings["group"]["eng"]]
    for x in message.author.roles:
        if x.id in ger_eng:
            group_id = settings['group'][input_group]
            group = get_role_by_id(message.channel.server, group_id)
            await client.add_roles(message.author, group)
            await private_msg(message, "Thanks for telling me that!")

async def remove_role(client, message, input_group):
    role_to_remove = get_role_by_id(message.channel.server, settings['group'][input_group])
    await client.remove_roles(message.author, role_to_remove)
    await private_msg(message, "Role removed.")


@register_command('ger', is_enabled=is_ex_server, description='Self-assign the Ger role.')
async def ger(client, message, args):
    group_id_german = settings['group']['ger']
    group_id_english = settings['group']['eng']
    group_ger = get_role_by_id(message.channel.server, group_id_german)
    group_eng = get_role_by_id(message.channel.server, group_id_english)
    await client.add_roles(message.author, group_ger)
    await asyncio.sleep(5)
    await client.remove_roles(message.author, group_eng)
    await private_msg(message, "Danke!")
    await delete_user_message(message)


@register_command('eng', is_enabled=is_ex_server, description='Self-assign the Eng role.')
async def eng(client, message, args):
    group_id_german = settings['group']['ger']
    group_id_english = settings['group']['eng']
    group_ger = get_role_by_id(message.channel.server, group_id_german)
    group_eng = get_role_by_id(message.channel.server, group_id_english)
    await client.add_roles(message.author, group_eng)
    await asyncio.sleep(5)
    await client.remove_roles(message.author, group_ger)
    await private_msg(message, "Thanks for telling me that!")
    await delete_user_message(message)


@register_command('role', is_enabled=is_ex_server, description='Add or remove a role.')
@add_argument("role", choices=role_list, help="Name of the role to add.")
@add_argument("--remove", action="store_true", help="Remove the role")
async def role_add_remove(client, message, args):
    if not args.remove:
        await add_role(client, message, args.role)
    else:
        await remove_role(client, message, args.role)
    await delete_user_message(message)
