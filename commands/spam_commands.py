import re
from utils import set_user_cooldown, user_cooldown
from handle_messages import delete_user_message, private_msg
from cmd_manager.decorators import register_command, add_argument

reg = re.compile(r"<:(\w+):(\d+)>")


@register_command(description='Converts your text into emoji characters')
@add_argument('text', help='Text too convert.')
async def memefont(client, message, args):
    await delete_user_message(message)
    if len(args.text) > 25:
        return await private_msg(message, "Max. 25 chars.")

    emoji = re.search(reg, args.text)
    if emoji:
        return await private_msg(message, "Emojis not allowed in the text.")

    if message.author in user_cooldown:
        return await private_msg(message, "Cooldown, wait 5min.")

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
