import json
from utils import get_role_by_id
from handle_messages import private_msg_user

with open("./config/role-settings.json") as f:
    settings = json.load(f)

roles = {
    u"\U0001F1E9\U0001F1EA": "ger",
    u"\U0001F1EC\U0001F1E7": "eng",
    u"\U0001F1EF\U0001F1F5": "jap",
    u"\U0001F51E": "nsfw",
    u"\U0001F4AE": "subs",
    u"\U0001F3B2": "games",
}
role_dict = settings["group"]


async def add_role(member, input_role):
    guild_role = get_role_by_id(member.guild, role_dict[roles[input_role]])
    await member.add_roles(guild_role)
    await private_msg_user(None, "Thanks for telling me that!", user=member)


async def find_role(member, input_role):
    needed_roles = [settings["group"]["ger"], settings["group"]["eng"], settings["group"]["jap"]]
    if input_role not in [u"\U0001F1E9\U0001F1EA", u"\U0001F1EC\U0001F1E7", u"\U0001F1EF\U0001F1F5"]:
        for role in member.roles:
            if role.id in needed_roles:  # ensure that the user has eng or ger role
                await add_role(member, input_role)
    else:
        await add_role(member, input_role)


async def remove_role(member, input_role):
    guild_role = get_role_by_id(member.guild, role_dict[roles[input_role]])
    await member.remove_roles(guild_role)
    await private_msg_user(None, "Role removed.", user=member)


async def role_handler(member, emoji, remove=False):
    if not remove:
        await find_role(member, emoji)
    else:
        await remove_role(member, emoji)
