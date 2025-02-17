import re
from utils import set_user_cooldown, user_cooldown, punish_user
from handle_messages import delete_user_message, private_msg
from cmd_manager.decorators import register_command, add_argument
from cmd_manager.filters import is_ex_server
from discord import File, HTTPException
from config import config
from utils import get_file
reg = re.compile(r"<:(\w+):(\d+)>")


@register_command(description='Converts your text into emoji characters')
@add_argument('text', help='Text too convert.')
async def memefont(client, message, args):
    await delete_user_message(message)
    if len(args.text) > 25:
        return await private_msg(message, "Only 25 characters are allowed.")

    emoji = re.search(reg, args.text)
    if emoji:
        return await private_msg(message, "Emotes are not allowed in the text.")

    if message.author in user_cooldown:
        return await private_msg(message, "Cooldown is still active, wait 5min.")

    set_user_cooldown(message.author, 300)

    text = args.text.lower()
    char_repl = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for i, j in char_repl.items():
        text = text.replace(i, j)
    char_map = {c: f":regional_indicator_{c}:"
                for c in map(chr, range(ord("a"), ord("z") + 1))}
    numwords = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    char_map.update({str(i): f":{name}:" for i, name in enumerate(numwords)})
    char_map[" "] = "  "

    emoji_text = "".join(char_map.get(c) or f"**{c}** " for c in text)

    if len(emoji_text) > 1950:
        emoji_text = f"{emoji_text[:1950]} .........truncated"
    await message.channel.send(f"From: {message.author.name}\n{emoji_text}")

@register_command(description="It's time to cool off.", is_enabled=is_ex_server)
@add_argument('--time', '-t', type=int, default=30, help="Duration in prison [in minutes]")
@add_argument('--reason', '-r', default="By Choice\N{TRADE MARK SIGN}", help="Reason for prison (optional)")
async def user_prison(client, message, args):
    # await delete_user_message(message)  # Don't delete to preserve context
    await punish_user(client, message, reason=args.reason, prison_length=args.time)
