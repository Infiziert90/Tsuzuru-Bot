import os
from discord import File
from config import config
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command

spam_folder = config.PICTURE.spam

# Spam images
for file in os.listdir(spam_folder):
    fn = os.path.splitext(file)[0]
    @register_command(fn, description=f'Post an image with content about {fn}')
    async def image_helper(_, message, args):
        await delete_user_message(message)

        f_name = filter(lambda f: f.startswith(args.command), os.listdir(spam_folder)).__next__()
        await message.channel.send(file=File(f"{spam_folder}{f_name}"), content=f"From: {message.author.display_name}")
