from persist import glob
from collections import defaultdict

import discord
from handle_messages import delete_user_message
from cmd_manager.filters import ex_feature_allowed
from cmd_manager.decorators import register_command, add_argument


class FaggotAlias:
    def __init__(self):
        self.client = None
        self.all_member = {}
        self.all_member_nick = {}
        #glob.faggot = defaultdict(int)
        #glob.alias = {}

    def init_client(self, client):
        self.client = client
        if not self.all_member:
            self.fill_member_list()

    def fill_member_list(self):
        for user in self.client.get_all_members():
            self.all_member[user.name.lower()] = user
            if user.nick:
                self.all_member_nick[user.nick.lower()] = user

    async def set_alias(self, channel, alias, username):
        user_obj = self.get_user_obj(username)

        if not user_obj:
            await self.client.send_message(channel, f"Cant find {username} in any list.")
            return

        if alias in glob.alias:
            await self.client.send_message(channel, f"{alias} is already in use.")
            return

        glob.alias[alias] = user_obj.name.lower()
        await self.client.send_message(channel, f"Added alias {alias} for user {user_obj.display_name}")

    async def blame_faggot(self, message, username):
        username = glob.alias.get(username, username)
        user_obj = self.get_user_obj(username)
        if not user_obj:
            await self.client.send_message(message.channel, f"Cant find {username} in any list.")
            return

        glob.faggot[user_obj.id] += 1
        await self.client.send_message(message.channel, f'{message.author.display_name} says that '
                                                        f'{user_obj.display_name} is a faggot.\nFaggot counter for '
                                                        f'{user_obj.display_name} is now {glob.faggot[user_obj.id]}.')

    def get_user_obj(self, username):
        user_obj = self.all_member.get(username, self.all_member_nick.get(username))
        if not user_obj:
            self.fill_member_list()
            user_obj = self.all_member.get(username, self.all_member_nick.get(username))
        return user_obj

    async def list_alias(self, channel):
        faggot_text = []
        for i, j in glob.alias.items():
            user_obj = self.get_user_obj(j)
            faggot_text.append(f"{i} = {user_obj.display_name}\n")
        faggot_text = ''.join(faggot_text)
        if len(faggot_text) > 1800:
            faggot_text = faggot_text[:1790] + "......."
        msn_embed = discord.Embed(title="Alias List:", description=faggot_text)
        await self.client.send_message(channel, embed=msn_embed)

    async def list_faggot(self, channel):
        faggot_text = ""
        user_dict = {user_obj.id: user_obj.display_name for user_obj in self.all_member.values()}
        for user_id, fag_count in list(glob.faggot.items()):
            user_obj = user_dict.get(user_id)
            if user_obj:
                faggot_text += f"{user_obj} = {fag_count}\n"
        if len(faggot_text) > 1800:
            faggot_text = faggot_text[:1790] + "......."
        msn_embed = discord.Embed(title="Faggot List:", description=faggot_text)
        await self.client.send_message(channel, embed=msn_embed)

faggot = FaggotAlias()


@register_command('alias', is_enabled=ex_feature_allowed, description='Define a short name for >>faggot.')
@add_argument('alias', type=str.lower, help='Alias for the user')
@add_argument('username', type=str.lower, help='Username for the alias')
async def create_alias(client, message, args):
    faggot.init_client(client)
    await delete_user_message(message)
    await faggot.set_alias(message.channel, args.alias, args.username)


@register_command('faggot', is_enabled=ex_feature_allowed, description='Blame a user as faggot.')
@add_argument('username', type=str.lower, help='Username from the faggot.')
async def blame_fa(client, message, args):
    faggot.init_client(client)
    await delete_user_message(message)
    await faggot.blame_faggot(message, args.username)


@register_command('list_alias', is_enabled=ex_feature_allowed, description='Shows the list of all alias.')
async def list_al(client, message, args):
    faggot.init_client(client)
    await delete_user_message(message)
    await faggot.list_alias(message.channel)


@register_command('list_faggot', is_enabled=ex_feature_allowed, description='Shows the list of all faggots.')
async def list_fa(client, message, args):
    faggot.init_client(client)
    await delete_user_message(message)
    await faggot.list_faggot(message.channel)
