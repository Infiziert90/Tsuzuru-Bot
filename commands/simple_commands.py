import random
import discord
from config import help_text
from functools import partial
from cmd_manager.bot_args import build_custom_help
from handle_messages import delete_user_message, private_msg
from cmd_manager.decorators import register_command, add_argument


@register_command('help', description='Show this help message.')
async def help_str(client, message, args):
    await delete_user_message(message)

    help_string = build_custom_help()
    # TODO split in better positions
    for val in [help_string[i:i + 1900] for i in range(0, len(help_string), 1900)]:
        await private_msg(message, f"```\n{val}```")


NAMES = [
    "Satan", "God", "Myself", "yuri", "GNU/Linux", "a brigher future", "hopelessness",
    "weeabooism", "Tatsuya", "eXmendiC (F*****T)", "Infi", "pipapo", "proprietary",
    "Arch", "trash"
]


@register_command(description='Select one of the given choices.')
@add_argument('choices', nargs='+')
async def choose(client, message, args):
    choice = random.choice(args.choices)
    name = random.choice(NAMES + [message.author.name])

    await message.channel.send(f"In the name of {name} I choose: {choice}")


async def text_handler(_, message, args, *, name, text):
    await delete_user_message(message)
    em = discord.Embed(title=f"Helpful links for {name}", description=text)
    await message.channel.send(embed=em)

for _name, _text in help_text("bot_bot").items():
    callback = partial(text_handler, name=_name, text=_text)
    register_command(_name, description=f"[Link] Helpful links for {_name}")(callback)
