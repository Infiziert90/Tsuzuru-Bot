import aiohttp
import discord
import asyncio
from string import Template
from handle_messages import private_msg_user, private_msg
from cmd_manager.decorators import register_command, add_argument


ongoing_votes = {}
num2emo = {0: "🇦", 1: "🇧", 2: "🇨", 3: "🇩", 4: "🇪", 5: "🇫", 6: "🇬", 7: "🇭", 8: "🇮", 9: "🇯"}
emo2num = {v: k for k, v in num2emo.items()}
language = {
    "en": {"win": "And the winner of $question is $winner", "draw": "$question is a draw between $winner"},
    "de": {"win": "Der Sieger von $question ist $winner", "draw": "$question ist ein Unentschieden zwischen $winner"},
}


class MessageDeletedException(Exception):
    def __repr__(self):
        return "Message deleted!"


@register_command('vote', description='Post a poll.')
@add_argument('topic', help='Question')
@add_argument('--time', '-t', type=int, default=60, help='Time [in Minutes]')
@add_argument('--multi_votes', '-m', dest='multi_votes', action='store_true', default=False, help='Allow multiple votes')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
@add_argument('--language', '-l', dest='lang', type=str.lower, default="en", choices=language.keys(), help='Set the language for the end text')
async def vote(_, message, args):
    if await check_message(message, args):
        return

    embed = discord.Embed(title=args.topic, description="Cast a vote by clicking the reactions.", color=0x000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time}mins")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    ongoing_votes[mes.id] = {
        "message": mes,
        "multi_votes": args.multi_votes,
        "voted_user": set(),
        "overflow": [],
        "anon": False,
    }

    for number in range(len(args.options)):
        await ongoing_votes[mes.id]["message"].add_reaction(num2emo[number])

    await run_vote(args.time, mes.id, ongoing_votes, args.lang)


@register_command('anon_vote', description='Post an anonymous poll.')
@add_argument('topic', help='Question')
@add_argument('--time', '-t', type=int, default=60, help='Time [in Minutes]')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
@add_argument('--language', '-l', dest='lang', type=str.lower, default="en", choices=language.keys(), help='Set the language for the end text')
async def anon_vote(_, message, args):
    if await check_message(message, args):
        return

    embed = discord.Embed(title=args.topic, description="Cast a vote secretly by clicking the reactions.", color=0000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time} min")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    ongoing_votes[mes.id] = {
        "message": mes,
        "multi_votes": False,
        "options": {k: 0 for k in range(len(args.options))},
        "voted_user": set(),
        "overflow": [],
        "anon": True,
    }

    for number in range(len(args.options)):
        await ongoing_votes[mes.id]["message"].add_reaction(num2emo[number])

    await run_vote(args.time, mes.id, args.lang)


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


async def get_message(mes_id, votes):
    try:
        votes[mes_id]["message"] = await votes[mes_id]["message"].channel.fetch_message(mes_id)
    except (discord.NotFound, discord.Forbidden):
        raise MessageDeletedException()  # raise error and delete the vote in the original function
    except (aiohttp.ClientConnectorError, discord.HTTPException):
        await asyncio.sleep(3)
        await get_message(mes_id, votes)


async def run_vote(time, mes_id, lang):
    try:
        # run until the timer is over
        for over in range(0, time, 2):
            await asyncio.sleep(120)
            await get_message(mes_id)
            embed = ongoing_votes[mes_id]["message"].embeds[0].set_footer(text=f"Time left: {time - over} min")
            await ongoing_votes[mes_id]["message"].edit(embed=embed)

        # get the current message object
        await get_message(mes_id)
        message = ongoing_votes[mes_id]["message"]

        embed = message.embeds[0].to_dict()
        winner = 0
        winners = []
        if not ongoing_votes[mes_id]["anon"]:
            for reaction in message.reactions:
                if reaction.me:
                    if reaction.count == winner:
                        winners.append(embed["fields"][emo2num[reaction.emoji]]["name"])
                    elif reaction.count > winner:
                        winners.clear()
                        winners.append(embed["fields"][emo2num[reaction.emoji]]["name"])
                        winner = reaction.count
        else:
            for k, v in ongoing_votes[mes_id]["options"].items():
                if v == winner:
                    winners.append(embed["fields"][k]["name"])
                elif v > winner:
                    winners.clear()
                    winners.append(embed["fields"][k]["name"])
                    winner = v

        if len(winners) == 1:
            content = Template(language[lang]['win']).substitute(question=message.embeds[0].title, winner=winners[0])
        else:
            content = Template(language[lang]['draw']).substitute(question=message.embeds[0].title,
                                                                  winner=''.join([f'{winner}, ' for winner in winners]))

        ongoing_votes.pop(mes_id)
        embed = discord.Embed.from_dict(embed)
        embed = embed.set_footer(text=f"Over!!!", icon_url=discord.Embed.Empty)
        await message.edit(content=content, embed=embed)
        await message.channel.send(content)
    except MessageDeletedException:
        return ongoing_votes.pop(mes_id)


async def remove_vote(reaction, message, user):
    # catch the internal remove process
    if user.id in ongoing_votes[message.id]["overflow"]:
        ongoing_votes[message.id]["overflow"].remove(user.id)
        return

    ongoing_votes[message.id]["voted_user"].discard(user.id)
    i = emo2num[reaction.emoji]
    embed = message.embeds[0].to_dict()
    embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    await message.edit(embed=discord.Embed.from_dict(embed))


async def valid_add(reaction, message, user):
    if user.id in ongoing_votes[message.id]["overflow"]:
        ongoing_votes[message.id]["overflow"].append(user.id)
        await reaction.remove(user)
        return False
    elif user.id in ongoing_votes[message.id]["voted_user"]:
        await private_msg_user(None, "Only 1 vote is allowed!", user)
        ongoing_votes[reaction.message.id]["overflow"].append(user.id)
        await reaction.remove(user)
        return False

    return True


async def add_vote(reaction, message, user):
    if not ongoing_votes[message.id]["multi_votes"] and not await valid_add(reaction, message, user):
        return

    ongoing_votes[message.id]["voted_user"].add(user.id)
    i = emo2num[reaction.emoji]
    embed = message.embeds[0].to_dict()
    embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    if ongoing_votes[message.id]["anon"]:
        await reaction.remove(user)
        ongoing_votes[message.id]["options"][i] += 1
        embed["fields"][i]["value"] = f"Votes: {ongoing_votes[message.id]['options'][i]}"
    else:
        embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    await message.edit(embed=discord.Embed.from_dict(embed))
