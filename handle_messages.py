import asyncio
import logging
import discord
import datetime
from config.globals import EX_LOG_CHANNEL


async def private_msg(message, content=None, embed=None, file=None, user=None):
    user = user or message.author
    try:
        await user.send(content=content, embed=embed, file=file)
    except (AttributeError, discord.Forbidden):
        if message is not None:
            del_message = await message.channel.send(
                content=f"{content or ''}\nSelf-Deleting in 5min.",
                embed=embed,
                file=file
            )
            asyncio.get_event_loop().call_later(300, lambda: asyncio.ensure_future(delete_user_message(del_message)))

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
    channel = client.get_channel(EX_LOG_CHANNEL)
    embed = discord.Embed(title=" ", description=desc, colour=colour)
    embed.set_author(name=title, icon_url=member.avatar_url)
    embed.set_footer(text=datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d'))
    await channel.send(embed=embed)

