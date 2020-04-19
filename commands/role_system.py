import json
from utils import get_role_by_id
from handle_messages import private_msg_user

with open("./config/role-settings.json") as f:
    settings = json.load(f)

# iemoji.com iOS 5 and higher
language_roles = {
    u"\U0001F1E9\U0001F1EA": "ger",
    u"\U0001F1EC\U0001F1E7": "eng",
    u"\U0001F1EF\U0001F1F5": "jap",
}
roles = dict(language_roles)
roles.update({
    u"\U0001F51E": "nsfw",
    u"\U0001F4AE": "subs",
    u"\U0001F3B2": "games",
    u"\U0001F921": "pol",
})
role_dict = settings["group"]
needed_roles = [
    settings["group"]["ger"],
    settings["group"]["eng"],
    settings["group"]["jap"]
]


def check_role(func):
    async def wrapper(member, emoji, add=True):
        # ensure that the user has eng, ger or jap role, when it is not a language role
        if emoji in language_roles or any(role.id in needed_roles for role in member.roles):
            return await func(member, emoji, add)
        await private_msg_user(None, "Language role is missing, pls select one!", user=member, retry_local=False)
    return wrapper


@check_role
async def role_handler(member, emoji, add=True):
    guild_role = get_role_by_id(member.guild, role_dict[roles[emoji]])
    await member.add_roles(guild_role) if add else await member.remove_roles(guild_role)
    await private_msg_user(None, f"{'Added' if add else 'Removed'} {emoji}", user=member, retry_local=False)
