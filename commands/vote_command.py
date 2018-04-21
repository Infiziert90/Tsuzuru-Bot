import discord
import asyncio
from handle_messages import private_msg_user, private_msg
from cmd_manager.decorators import register_command, add_argument


ongoing_votes = {"anon": False}
anon_votes = {"anon": True}
num2emo = {1: "1⃣", 2: "2⃣", 3: "3⃣", 4: "4⃣", 5: "5⃣", 6: "6⃣", 7: "7⃣", 8: "8⃣", 9: "9⃣", 0: "0⃣"}
emo2num = {v: k for k, v in num2emo.items()}


@register_command('vote', description='Post a poll.')
@add_argument('topic', help='Question')
@add_argument('time', type=int, default=30, help='Time')
@add_argument('--multi', '-m', dest='multi', action='store_true', default=False, help='Allow multiple votes')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
async def vote(_, message, args):
    if len(ongoing_votes) == 3:
        return await private_msg(message, "Too many ongoing votes. Please wait until one is over.")

    if args.time > 1440 or args.time < 10:
        return await private_msg(message, "Time must be between 10 and 1440.")

    if len(args.options) > 10:
        return await private_msg(message, "You cannot add more than 10 options.")

    embed = discord.Embed(title=args.topic, description="Cast a vote by clicking one of the reactions.", color=0x000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time}mins")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    ongoing_votes[mes.id] = {
        "m": mes,
        "multi": args.multi,
        "voted_user": set(),
        "overflow": [],
    }

    for number in range(len(args.options)):
        await ongoing_votes[mes.id]["m"].add_reaction(num2emo[number])

    await vote_timer(args.time, mes.id, ongoing_votes)


@register_command('anon_vote', description='Post an anonymous poll.')
@add_argument('topic', help='Question')
@add_argument('time', type=int, default=30, help='Time')
@add_argument('--options', '-o', dest='options', required=True, action='append', help='Available options, can be used multiple times')
async def anon_vote(_, message, args):
    if len(anon_votes) == 3:
        return await private_msg(message, "Too many ongoing anonymous votes. Please wait until one is over.")

    if args.time > 1440 or args.time < 10:
        return await private_msg(message, "Time must be between 10 and 1440.")

    if len(args.options) > 10:
        return await private_msg(message, "You cannot add more than 10 options.")

    embed = discord.Embed(title=args.topic, description="Cast a vote secretly by clicking one of the reactions.", color=0x000000)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_footer(text=f"Time left: {args.time}mins")
    for option, number in zip(args.options, range(len(args.options))):
        embed.add_field(name=f"{num2emo[number]} {option}", value=f"Votes: 0", inline=False)

    mes = await message.channel.send(embed=embed)
    anon_votes[mes.id] = {
        "m": mes,
        "multi": False,
        "options": {k: 0 for k in range(len(args.options))},
        "voted_user": set(),
        "overflow": [],
    }

    for number in range(len(args.options)):
        await anon_votes[mes.id]["m"].add_reaction(num2emo[number])

    await vote_timer(args.time, mes.id, anon_votes)


async def get_message(mes_id, vo):
    vo[mes_id]["m"] = await vo[mes_id]["m"].channel.get_message(mes_id)


async def vote_timer(time, mes_id, vo):
    time_left = time
    for _ in range(0, time, 1):
        await asyncio.sleep(60)
        await get_message(mes_id, vo)
        time_left -= 1
        embed = vo[mes_id]["m"].embeds[0].set_footer(text=f"Time left: {time_left}mins")
        await vo[mes_id]["m"].edit(embed=embed)

    await get_message(mes_id, vo)
    m = vo[mes_id]["m"]

    winner = 0
    winners = []
    if not vo["anon"]:
        for reaction in m.reactions:
            if reaction.me:
                if reaction.count == winner:
                    winners.append(m.embeds[0]._fields[emo2num[reaction.emoji]]["name"])
                elif reaction.count > winner:
                    winners.clear()
                    winners.append(m.embeds[0]._fields[emo2num[reaction.emoji]]["name"])
                    winner = reaction.count
    else:
        for k, v in vo[mes_id]["options"].items():
            if v == winner:
                winners.append(m.embeds[0]._fields[k]["name"])
            elif v > winner:
                winners.clear()
                winners.append(m.embeds[0]._fields[k]["name"])
                winner = v

    if len(winners) == 1:
        content = f"And the winner of **{m.embeds[0].title}** is **{winners[0]}**"
    else:
        content = f"And the winners of **{m.embeds[0].title}** are "
        for winner in winners:
            content += f"**{winner}**, "

    vo.pop(mes_id)
    embed = m.embeds[0].set_footer(text=f"Over!!!", icon_url=discord.Embed.Empty)
    await m.edit(content=content, embed=embed)
    await m.channel.send(content)


async def remove_vote(reaction, user, vo):
    if user.id in vo[reaction.message.id]["overflow"]:
        vo[reaction.message.id]["overflow"].remove(user.id)
        return

    vo[reaction.message.id]["voted_user"].discard(user.id)
    i = emo2num[reaction.emoji]
    m = reaction.message
    embed = m.embeds[0].set_field_at(i, name=m.embeds[0]._fields[i]["name"], value=f"Votes: {reaction.count-1}", inline=False)
    await m.edit(embed=embed)


async def check_add_vote(reaction, user, vo):
    if user.id in vo[reaction.message.id]["overflow"]:
        vo[reaction.message.id]["overflow"].append(user.id)
        await reaction.message.remove_reaction(reaction, user)
        return False
    elif user.id in vo[reaction.message.id]["voted_user"]:
        await private_msg_user(reaction.message, "Only 1 vote is allowed", user)
        vo[reaction.message.id]["overflow"].append(user.id)
        await reaction.message.remove_reaction(reaction, user)
        return False

    return True


async def add_vote(reaction, user, vo):
    if not vo[reaction.message.id]["multi"] and not await check_add_vote(reaction, user, vo):
        return

    vo[reaction.message.id]["voted_user"].add(user.id)
    i = emo2num[reaction.emoji]
    m = reaction.message
    if vo["anon"]:
        await reaction.message.remove_reaction(reaction, user)
        vo[m.id]["options"][i] += 1
        embed = m.embeds[0].set_field_at(i, name=m.embeds[0]._fields[i]["name"], value=f"Votes: {vo[m.id]['options'][i]}", inline=False)
    else:
        embed = m.embeds[0].set_field_at(i, name=m.embeds[0]._fields[i]["name"], value=f"Votes: {reaction.count-1}", inline=False)
    await m.edit(embed=embed)




