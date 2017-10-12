import json
from handle_messages import private_msg
from utils import get_role_by_id, has_role
from cmd_manager.filters import is_ex_server
from cmd_manager.decorators import register_command, add_argument

with open("./config/avs-bot-settings.json") as f:
    settings = json.load(f)


@register_command('avs', is_enabled=is_ex_server, description='Add role AVS.')
@add_argument("--expert", nargs="+", metavar="mention", help="Add expert AVS role (only usable by AVS experts)")
@add_argument("--remove", action="store_true", help="Remove all AVS roles")
async def avs(client, message, args):
    group_id = settings['group']['avs']
    expert_id = settings['group']['avs-expert']
    group = get_role_by_id(message.channel.server, group_id)
    expert = get_role_by_id(message.channel.server, expert_id)

    if args.expert:
        if not has_role(message.author, expert_id):
            await private_msg(message.author, "You need to be an expert to do that.")
        elif args.remove:
            for mention in message.mentions:
                await client.remove_roles(mention, expert)
                await private_msg(mention, "You are no longer an AVS expert.")
        else:
            for mention in message.mentions:
                await client.add_roles(mention, expert)
                await private_msg(mention, "Welcome to the AVS experts!")
    else:
        if args.remove:
            await client.remove_roles(message.author, group)
        else:
            await client.add_roles(message.author, group)


@register_command('vs', is_enabled=is_ex_server, description='Add role VS.')
@add_argument("--expert", nargs="+", metavar="mention", help="Add expert VS role (only usable by VS experts)")
@add_argument("--remove", action="store_true", help="Remove all VS roles")
async def vs(client, message, args):
    group_id = settings['group']['vs']
    expert_id = settings['group']['vs-expert']
    group = get_role_by_id(message.channel.server, group_id)
    expert = get_role_by_id(message.channel.server, expert_id)

    if args.expert:
        if not has_role(message.author, expert_id):
            await private_msg(message.author, "You need to be an expert to do that.")
        elif args.remove:
            for mention in message.mentions:
                await client.remove_roles(mention, expert)
                await private_msg(mention, "You are no longer an VS expert.")
        else:
            for mention in message.mentions:
                await client.add_roles(mention, expert)
                await private_msg(mention, "Welcome to the VS experts!")
    else:
        if args.remove:
            await client.remove_roles(message.author, group)
        else:
            await client.add_roles(message.author, group)
