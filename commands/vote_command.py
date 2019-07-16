import aiohttp
import discord
import asyncio
from handle_messages import private_msg_user, private_msg
from cmd_manager.decorators import register_command, add_argument


ongoing_votes = {}
anon_votes = {}
num2emo = {0: "🇦", 1: "🇧", 2: "🇨", 3: "🇩", 4: "🇪", 5: "🇫", 6: "🇬", 7: "🇭", 8: "🇮", 9: "🇯"}
emo2num = {v: k for k, v in num2emo.items()}
language = {
    "en": ["And the winner of", "is", "And the winners of", "are"],
    "de": ["Der Sieger von", "ist", "Die Sieger von", "sind"],
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
    if await check_message(message, args, ongoing_votes):
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
    if await check_message(message, args, anon_votes):
        return

    embed = discord.Embed(title=args.topic, description="Cast a vote secretly by clicking the reactions.", color=0000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time} min")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    anon_votes[mes.id] = {
        "message": mes,
        "multi_votes": False,
        "options": {k: 0 for k in range(len(args.options))},
        "voted_user": set(),
        "overflow": [],
        "anon": True,
    }

    for number in range(len(args.options)):
        await anon_votes[mes.id]["message"].add_reaction(num2emo[number])

    await run_vote(args.time, mes.id, anon_votes, args.lang)


async def check_message(message, args, vo):
    if len(vo) == 5:
        return await private_msg(message, "Too many ongoing votes. Please wait until one is over.")

    if args.time < 5:
        return await private_msg(message, "Time must be over 5")

    if len(args.options) > 10 or len(args.options) < 1:
        return await private_msg(message, "Options must be between 2 and 10.")

    options = [x.lower() for x in args.options]
    if len(set(options)) != len(options):
        return await private_msg(message, "Options must be unique.")

    return False


async def get_message(mes_id, votes):
    try:
        votes[mes_id]["message"] = await votes[mes_id]["message"].channel.fetch_message(mes_id)
    except (discord.NotFound, discord.Forbidden):
        raise MessageDeletedException()  # raise error and delete the vote in the original function
    except (aiohttp.ClientConnectorError, discord.HTTPException):
        await asyncio.sleep(3)
        await get_message(mes_id, votes)


async def run_vote(time, mes_id, vo, lang):
    try:
        # run until the timer is over
        for over in range(0, time, 2):
            await asyncio.sleep(120)
            await get_message(mes_id, vo)
            embed = vo[mes_id]["message"].embeds[0].set_footer(text=f"Time left: {time - over} min")
            await vo[mes_id]["message"].edit(embed=embed)

        # get the current message object
        await get_message(mes_id, vo)
        message = vo[mes_id]["message"]

        embed = message.embeds[0].to_dict()
        winner = 0
        winners = []
        if not vo[mes_id]["anon"]:
            for reaction in message.reactions:
                if reaction.me:
                    if reaction.count == winner:
                        winners.append(embed["fields"][emo2num[reaction.emoji]]["name"])
                    elif reaction.count > winner:
                        winners.clear()
                        winners.append(embed["fields"][emo2num[reaction.emoji]]["name"])
                        winner = reaction.count
        else:
            for k, v in vo[mes_id]["options"].items():
                if v == winner:
                    winners.append(embed["fields"][k]["name"])
                elif v > winner:
                    winners.clear()
                    winners.append(embed["fields"][k]["name"])
                    winner = v

        if len(winners) == 1:
            content = f"{language[lang][0]} **{message.embeds[0].title}** {language[lang][1]} **{winners[0]}**"
        else:
            content = f"{language[lang][2]} **{message.embeds[0].title}** {language[lang][3]}" \
                      f" {''.join([f'**{winner}**, ' for winner in winners])}"

        vo.pop(mes_id)
        embed = discord.Embed.from_dict(embed)
        embed = embed.set_footer(text=f"Over!!!", icon_url=discord.Embed.Empty)
        await message.edit(content=content, embed=embed)
        await message.channel.send(content)
    except MessageDeletedException:
        return vo.pop(mes_id)


async def remove_vote(reaction, user, vo):
    # catch the internal remove process
    if user.id in vo[reaction.message.id]["overflow"]:
        vo[reaction.message.id]["overflow"].remove(user.id)
        return

    vo[reaction.message.id]["voted_user"].discard(user.id)
    i = emo2num[reaction.emoji]
    message = reaction.message
    embed = message.embeds[0].to_dict()
    embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    await message.edit(embed=discord.Embed.from_dict(embed))


async def check_add_vote(reaction, user, vo):
    if user.id in vo[reaction.message.id]["overflow"]:
        vo[reaction.message.id]["overflow"].append(user.id)
        await reaction.message.remove_reaction(reaction, user)
        return False
    elif user.id in vo[reaction.message.id]["voted_user"]:
        await private_msg_user(reaction.message, "Only 1 vote is allowed!", user)
        vo[reaction.message.id]["overflow"].append(user.id)
        await reaction.message.remove_reaction(reaction, user)
        return False

    return True


async def add_vote(reaction, user, vo):
    if not vo[reaction.message.id]["multi_votes"] and not await check_add_vote(reaction, user, vo):
        return

    vo[reaction.message.id]["voted_user"].add(user.id)
    i = emo2num[reaction.emoji]
    message = reaction.message
    embed = message.embeds[0].to_dict()
    embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    if vo[message.id]["anon"]:
        await reaction.message.remove_reaction(reaction, user)
        vo[message.id]["options"][i] += 1
        embed["fields"][i]["value"] = f"Votes: {vo[message.id]['options'][i]}"
    else:
        embed["fields"][i]["value"] = f"Votes: {reaction.count-1}"
    await message.edit(embed=discord.Embed.from_dict(embed))
