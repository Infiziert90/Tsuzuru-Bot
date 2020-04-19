import json
from utils import get_role_by_id
from handle_messages import private_msg

with open("./config/role-settings.json") as f:
    settings = json.load(f)

# iemoji.com iOS 5 and higher
language_emotes = settings["language_emotes"]
emotes = {**language_emotes, **settings["other_emotes"]}
needed_roles = settings["languages_roles"]
role_dict = {**needed_roles, **settings["other_roles"]}


def check_role(func):
    async def wrapper(member, emoji, add=True):
        # ensure that the user has eng, ger or jap role, when it is not a language role
        if emoji in language_emotes or any(role.id in needed_roles.values() for role in member.roles):
            return await func(member, emoji, add)
        await private_msg(None, content="Language role is missing, pls select one!", user=member)
    return wrapper


@check_role
async def role_handler(member, emoji, add=True):
    guild_role = get_role_by_id(member.guild, role_dict[emotes[emoji]])
    await member.add_roles(guild_role) if add else await member.remove_roles(guild_role)
    await private_msg(None, content=f"{'Added' if add else 'Removed'} {emoji}", user=member)
