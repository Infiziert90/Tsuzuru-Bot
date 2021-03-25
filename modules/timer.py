import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import re
from typing import Any, Dict, List, Optional

import discord
import dateutil.parser

from cmd_manager.decorators import register_command, add_argument
import storage


########################################


TIME_PATTERN = re.compile(
    r"^"
    r"(?:(?P<d>\d+)[dD])?"
    r"(?:(?P<h>\d+)[hH])?"
    r"(?:(?P<m>\d+)[mM])?"
    r"(?:(?P<s>\d+)[sS]?)?"
    r"$"
)
UNIT_SCALES = [
    ("s", 60),
    ("m", 60),
    ("h", 24),
    ("d", 1_000_000_000),  # maximum of timedelta
]


def parse_timedelta(time_string: str) -> Optional[timedelta]:
    match = TIME_PATTERN.match(time_string)
    if match is None:
        return None
    d, h, m, s = map(int, match.groups("0"))
    return timedelta(days=d, hours=h, minutes=m, seconds=s)


def format_timedelta(delta: timedelta) -> str:
    carry = int(delta.total_seconds())
    s = []
    for suffix, scale in UNIT_SCALES:
        carry, remainder = divmod(carry, scale)
        if remainder:
            s.append(f"{remainder}{suffix}")
    return "".join(reversed(s))


def parse_datetime(time_string: str) -> Optional[datetime]:
    try:
        return dateutil.parser.parse(time_string)
    except ValueError:
        return None


########################################

NO_MENTIONS = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)

data: Dict[str, Any] = {}
handles: Dict[int, asyncio.Handle] = {}


async def init(client):
    global data
    data = storage.storage.setdefault('timer_data', {})
    data.setdefault('last_id', 0)
    data.setdefault('timers', {})

    now = datetime.now()
    for timer in list(data['timers'].values()):
        if timer.timestamp < now:
            await send_reminder(client, timer)
        else:
            schedule(client, timer)


# Could be stored in a database,
# but let's keep it simple and use pickle instead.
@dataclass
class Timer:
    id: int = field(init=False)
    timestamp: datetime
    guild_id: Optional[int]
    channel_id: int
    message_id: int
    user_id: int
    text: str

    def __post_init__(self):
        data['last_id'] += 1
        self.id = data['last_id']


async def send_reminder(client, timer: Timer):
    handles.pop(timer.id, None)
    del data['timers'][timer.id]
    storage.save()

    channel = client.get_channel(timer.channel_id)
    if not channel:
        logging.error(f"Cannot find channel for {timer}")
        return

    text = timer.text or "I am visiting from the past to remind you of something."
    text = f"<@{timer.user_id}> {text}"
    now = datetime.now()
    if now > timer.timestamp + timedelta(seconds=5):
        text = f"{text} ({format_timedelta(now - timer.timestamp)} late)"
    reference = discord.MessageReference(
        message_id=timer.message_id,
        channel_id=timer.channel_id,
        guild_id=timer.guild_id,
    )
    await channel.send(text, reference=reference, mention_author=True)
    # TODO what about failure? schedule retry? retry on next startup? how often?


def schedule(client, timer):
    loop = asyncio.get_running_loop()
    # Requires Python 3.8 for delays of 1 day or higher
    handles[timer.id] = loop.call_later(
        (timer.timestamp - datetime.now()).total_seconds(),
        lambda: loop.create_task(send_reminder(client, timer)),
    )


@register_command(description="Schedule a timer.")
@add_argument('timestamp',
              help="When the timer should trigger. Accepts a variety of formats."
                   " Relative time may be given in the format '10h30m'.")
@add_argument('text', nargs='?', default=None,
              help="Text to send when the timer runs out. May include mentions.")
async def timer(client, message, args):
    now = datetime.now()
    delta = parse_timedelta(args.timestamp)
    if not delta:
        timestamp = parse_datetime(args.timestamp)
        if not timestamp:
            await message.channel.send("Unable to parse timestamp.", reference=message)
            return
        delta = timestamp - now
    else:
        timestamp = now + delta

    if timestamp <= now:
        await message.channel.send(
            f"This timestamp is in the past (by **{format_timedelta(-delta)}**)",
            reference=message,
        )
        return

    timer = Timer(
        timestamp=timestamp,
        guild_id=message.guild.id if message.guild else None,
        channel_id=message.channel.id,
        message_id=message.id,
        user_id=message.author.id,
        text=args.text,
    )
    data['timers'][timer.id] = timer
    storage.save()
    schedule(client, timer)

    await message.channel.send(
        f"I will remind you in **{format_timedelta(delta)}** ({timestamp:%Y-%m-%d %H:%M:%S%z});"
        f" ID: {timer.id}",
        reference=message,
        mention_author=False,
    )


@register_command(description="List your scheduled timers.")
async def timers(client, message, args):
    timers = [r for r in data['timers'].values() if r.user_id == message.author.id]
    if timers:
        timers.sort(key=lambda r: r.timestamp)
        now = datetime.now()
        delta_texts = [format_timedelta(r.timestamp - now) for r in timers]
        delta_length = max(map(len, delta_texts))
        id_length = len(str(max(r.id for r in timers)))
        raw = "\n".join(
            f"{r.id:>{id_length}}"
            f" | {delta_text:>{delta_length}}"
            f" | {r.timestamp:%Y-%m-%d %H:%M:%S%z}"
            f" | {r.text}"
            for r, delta_text in zip(timers, delta_texts)
        )
        text = f"```md\n{raw}\n```"
    else:
        text = "No timers to show."
    await message.channel.send(
        text,
        reference=message,
        allowed_mentions=NO_MENTIONS,
    )


@register_command(description="Deschedule a timer by id.")
@add_argument('ids', nargs='+',
              help="Timer ids to be descheduled. Use 'all' to unschedule all your timers.")
async def timer_remove(client, message, args):
    bad_ids: List[str] = []

    if args.ids == ['all']:
        for id_, r in list(data['timers'].items()):
            if r.user_id == message.author.id:
                del data['timers'][id_]
                handles.pop(id_).cancel()

    else:
        for idstr in args.ids:  # type: str
            try:
                id_ = int(idstr)
            except ValueError:
                bad_ids.append(idstr)
            else:
                r = data['timers'].get(id_)
                if r and r.user_id == message.author.id:
                    del data['timers'][id_]
                    handles.pop(id_).cancel()
                else:
                    bad_ids.append(idstr)

    if bad_ids:
        await message.channel.send(
            f"Unable to deschedule: {', '.join(bad_ids)}",
            reference=message,
            mention_author=False,
        )
    else:
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
