import aiohttp
import discord
import asyncio
from string import Template
from handle_messages import private_msg_user, private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument

ongoing_votes = {}
num2emo = {0: "🇦", 1: "🇧", 2: "🇨", 3: "🇩", 4: "🇪", 5: "🇫", 6: "🇬", 7: "🇭", 8: "🇮", 9: "🇯"}
emo2num = {v: k for k, v in num2emo.items()}
languages = {
    "en": {"win": "And the winner of $question is $winner", "draw": "$question is a draw between $winner"},
    "de": {"win": "Der Sieger von $question ist $winner", "draw": "$question ist ein Unentschieden zwischen $winner"},
}


class MessageDeletedException(Exception):
    def __repr__(self):
        return "Message deleted!"


@register_command(description='Cancel your vote')
@add_argument('message_id', type=int, help='Message id from the bot message')
async def cancel_vote(_, message, args):
    await delete_user_message(message)
    if ongoing_votes[args.message_id].creator_id != message.author.id:
        return await private_msg(message, "This is not your vote!")

    await ongoing_votes[args.message_id].message.delete()
    return ongoing_votes.pop(args.message_id, None)


@register_command('vote', description='Post a poll.')
@add_argument('topic', help='Question')
@add_argument('--time', '-t', type=int, default=60, help='Time [in Minutes]')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
@add_argument('--language', '-l', dest='lang', type=str.lower, default="en", choices=languages.keys(), help='Set the language for the end text')
async def normal_vote(_, message, args):
    return await create_vote(message, args, anon=False)


@register_command(description='Post an anonymous poll.')
@add_argument('topic', help='Question')
@add_argument('--time', '-t', type=int, default=60, help='Time [in Minutes]')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
@add_argument('--language', '-l', dest='lang', type=str.lower, default="en", choices=languages.keys(), help='Set the language for the end text')
async def anon_vote(_, message, args):
    return await create_vote(message, args, anon=True)


async def check_message(message, args):
    if len(ongoing_votes) == 5:
        return await private_msg(message, "Too many ongoing votes. Please wait until one is over.")

    if args.time < 5:
        return await private_msg(message, "Time must be over 5")

    if len(args.options) > 10 or len(args.options) < 1:
        return await private_msg(message, "Options must be between 2 and 10.")

    options = [x.lower() for x in args.options]
    if len(set(options)) != len(options):
        return await private_msg(message, "Options must be unique.")

    if len(args.topic) >= 250:
        return await private_msg(message, "Topic can't be over 250 characters long.")

    return False


async def create_vote(message, args, anon):
    if await check_message(message, args):
        return

    embed = discord.Embed(title=args.topic, description=f"Cast a vote {'secretly' if anon else ''} "
                                                        f"by clicking the reactions.", color=0000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time} min")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    handler = VoteHandler(mes, args.options, args.lang, message.author.id, anon=anon)
    ongoing_votes[mes.id] = handler

    for number in range(len(args.options)):
        await mes.add_reaction(num2emo[number])

    asyncio.create_task(handler.vote_timer(args.time))


class Vote:
    def __init__(self, user, reaction, added=True):
        self.user: discord.Member = user
        self.reaction: discord.Reaction = reaction
        self.added: bool = added

    async def remove(self):
        return await self.reaction.remove(self.user)


class VoteHandler:
    def __init__(self, message, options, language, creator_id, anon=False):
        self.message: discord.Message = message
        self.votes_per_options: dict = {k: set() for k in range(len(options))}
        self.language: str = language
        self.creator_id = creator_id
        self.anon: bool = anon

        self.users: set = set()
        self.overflow: list = []
        self.task: asyncio.Task = asyncio.Task(self.processing_worker())
        self.queue: asyncio.Queue = asyncio.Queue()

    async def store_vote(self, vote: Vote):
        return await self.queue.put(vote)

    async def processing_worker(self):
        while True:
            try:
                vote = await self.queue.get()
                if vote.added:
                    await self.added_vote(vote)
                else:
                    await self.removed_vote(vote)
                self.queue.task_done()
            except asyncio.CancelledError:
                return

    async def removed_vote(self, vote: Vote):
        # catch the internal remove process
        if vote.user.id in self.overflow:
            self.overflow.remove(vote.user.id)
            return

        # get the latest message object
        await self.get_message()
        self.users.discard(vote.user.id)

        # check if the user is still in the reactions or if the bot already deleted it
        i = emo2num[vote.reaction.emoji]
        if vote.user.id in self.votes_per_options[i]:
            self.votes_per_options[i].remove(vote.user.id)
            embed = self.veracity_check()
            await self.message.edit(embed=discord.Embed.from_dict(embed))

    async def added_vote(self, vote: Vote):
        if not await self.validate_add(vote):
            return

        # get the latest message object
        await self.get_message()

        self.users.add(vote.user.id)
        if self.anon:
            self.overflow.append(vote.user.id)
            await vote.remove()

        i = emo2num[vote.reaction.emoji]
        self.votes_per_options[i].add(vote.user.id)

        embed = self.veracity_check()
        await self.message.edit(embed=discord.Embed.from_dict(embed))

    async def validate_add(self, vote: Vote):
        if vote.user.id in self.overflow:
            self.overflow.append(vote.user.id)
            await vote.remove()
            return False
        elif vote.user.id in self.users:
            await private_msg_user(None, "Only 1 vote is allowed!", vote.user)
            self.overflow.append(vote.user.id)
            await vote.remove()
            return False

        return True

    def veracity_check(self):
        embed = self.message.embeds[0].to_dict()

        for reaction in self.message.reactions:
            if reaction.me:
                i = emo2num[reaction.emoji]
                embed["fields"][i]["value"] = f"Votes: {len(self.votes_per_options[i])}"

        return embed

    async def get_message(self):
        while True:
            try:
                self.message = await self.message.channel.fetch_message(self.message.id)
                return
            except (discord.NotFound, discord.Forbidden):
                raise MessageDeletedException()  # raise error and delete the vote in the original function
            except (aiohttp.ClientConnectorError, discord.HTTPException):
                await asyncio.sleep(3)

    async def vote_timer(self, time):
        try:
            # run until the timer is over
            for over in range(0, time, 1):
                await asyncio.sleep(60)
                await self.get_message()
                embed = self.veracity_check()
                embed = discord.Embed.from_dict(embed).set_footer(text=f"Time left: {time - over} min")
                await self.message.edit(embed=embed)

            # get the latest message object
            await self.get_message()
        except (MessageDeletedException, asyncio.CancelledError):
            self.task.cancel()
            return ongoing_votes.pop(self.message.id, None)

        await self.queue.join()
        self.task.cancel()
        ongoing_votes.pop(self.message.id, None)

        return await self.vote_result()

    async def vote_result(self):
        embed = self.message.embeds[0].to_dict()
        winner = 0
        winners = []
        for k, v in self.votes_per_options.items():
            v = len(v)
            if v == winner:
                winners.append(embed["fields"][k]["name"])
            elif v > winner:
                winners.clear()
                winners.append(embed["fields"][k]["name"])
                winner = v

        title = self.message.embeds[0].title
        content = Template(languages[self.language]['win' if len(winners) == 1 else 'draw'])
        content = content.substitute(question=title, winner=''.join([f'{winner}, ' for winner in winners]))

        embed = discord.Embed.from_dict(embed)
        embed = embed.set_footer(text=f"Over!!!", icon_url=discord.Embed.Empty)
        await self.message.edit(content=content, embed=embed)

        return await self.message.channel.send(content)
