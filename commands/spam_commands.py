import re
from utils import set_user_cooldown, user_cooldown
from handle_messages import delete_user_message, private_msg
from cmd_manager.decorators import register_command, add_argument

reg = re.compile(r"<:(\w+):(\d+)>")


@register_command('memefont', description='Converts your text into emojis')
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

    chars = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    alpha = [chr(x) for x in range(ord("a"), ord("z") + 1)]
    num2words = {"1": 'one', "2": 'two', "3": 'three', "4": 'four', "5": 'five', "6": 'six', "7": 'seven',
                 "8": 'eight', "9": 'nine', "0": "zero"}
    text = args.text.lower()
    for i, j in chars.items():
        text = text.replace(i, j)

    emoji_text = ""
    for c in text:
        if c in alpha:
            emoji_text += f":regional_indicator_{c}:"
        elif c in num2words:
            emoji_text += f":{num2words[c]}:"
        elif c != " ":
            emoji_text += f"**{c}** "
        else:
            emoji_text += "  "

    if len(emoji_text) > 1950:
        await message.channel.send(f"From: {message.author.display_name}\n{emoji_text[:1950]} .........truncated")
    else:
        await message.channel.send(f"From: {message.author.display_name}\n{emoji_text}")
