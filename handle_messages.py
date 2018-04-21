#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import logging
import discord


async def handle_msg(message, content=None, embed=None, file=None, user=None):
    user = user or message.author
    try:
        await user.send(content=content, embed=embed, file=file)
    except (AttributeError, discord.Forbidden):
        del_message = await message.channel.send(content=f"{content or ''}\n\nThis Message will be deleted in 5min.",  embed=embed, file=file)
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


async def private_msg_user(message, answer, user):
    await handle_msg(message, content=answer, user=user)
    return True


async def delete_user_message(message):
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass
