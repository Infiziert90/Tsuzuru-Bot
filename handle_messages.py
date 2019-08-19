import asyncio
import logging
import discord
import datetime


async def handle_msg(message, content=None, embed=None, file=None, user=None, retry_local=True):
    user = user or message.author
    try:
        await user.send(content=content, embed=embed, file=file)
    except (AttributeError, discord.Forbidden):
        if retry_local:
            del_message = await message.channel.send(content=f"{content or ''}\nThis Message will be deleted in 5min.",
                                                     embed=embed, file=file)
            asyncio.get_event_loop().call_later(300, lambda: asyncio.ensure_future(delete_user_message(del_message)))


async def private_msg(message, answer):
    await handle_msg(message, content=answer)
    return True


async def private_msg_embed(message, answer):
    await handle_msg(message, embed=answer)
    return True


async def private_msg_code(message, answer):
    await handle_msg(message, content=f"```\n{answer}```")
    return True


async def private_msg_file(message, file, content=None):
    await handle_msg(message, file=discord.File(file), content=content)
    return True


async def private_msg_user(message, answer, user, retry_local=True):
    await handle_msg(message, content=answer, user=user, retry_local=retry_local)
    return True


async def delete_user_message(message):
    if isinstance(message.channel, discord.abc.GuildChannel):
        try:
            await message.delete()
        except discord.Forbidden as err:
            logging.warning(f"Exception while deleting a message: {err}")
        except discord.NotFound as err:
            logging.debug(f"Exception while deleting a message: {err}")


async def send_log_message(client, member, title, desc=discord.Embed.Empty, colour=discord.Colour.green()):
    channel = client.get_channel(338293663677546496)
    embed = discord.Embed(title=" ", description=desc, colour=colour)
    embed.set_author(name=title, icon_url=member.avatar_url)
    embed.set_footer(text=datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d'))
    await channel.send(embed=embed)

