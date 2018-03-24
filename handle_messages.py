#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import discord


def message_init(new_client):
    global client
    client = new_client


async def handle_msg(message, content=None, embed=None, func=None, user=None):
    func = func or client.send_message
    user = user or message.author
    try:
        msg_answer = await client.start_private_message(user)
        await func(msg_answer, content=content, embed=embed)
    except (AttributeError, discord.Forbidden):
        del_message = await func(message.channel, content=f"{content or ''}\n\nThis Message will be deleted in 5min.",  embed=embed)
        asyncio.get_event_loop().call_later(300, lambda: asyncio.ensure_future(delete_user_message(del_message)))


async def private_msg(message, answer):
    await handle_msg(message, content=answer)


async def private_msg_embed(message, embed):
    await handle_msg(message, embed=embed)


async def private_msg_code(message, text):
    await handle_msg(message, content=f"```\n{text}```")


async def private_msg_file(message, file, content):
    async def _send_file_without_embed(msg, embed=None, **kwargs):
        return await client.send_file(msg, file, **kwargs)
    await handle_msg(message, content, func=_send_file_without_embed)


async def private_msg_user(message, answer, user):
    await handle_msg(message, content=answer, user=user)


async def wait_for_message(message):
    return await client.wait_for_message(author=message.author)


async def delete_user_message(message):
    try:
        await client.delete_message(message)
    except (discord.Forbidden, discord.NotFound):
        pass
