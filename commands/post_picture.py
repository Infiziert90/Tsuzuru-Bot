from pathlib import Path
from functools import partial
from discord import File
from config import config
from handle_messages import delete_user_message
from cmd_manager.decorators import register_command

spam_folder = config.PICTURE.spam
spam_path = Path(spam_folder)

if spam_folder and spam_path.is_dir():

    async def image_handler(_, message, args, *, file):
        await delete_user_message(message)
        await message.channel.send(file=file, content=f"From: {message.author.name}")

    for img_path in spam_path.iterdir():
        callback = partial(image_handler, file=File(img_path))
        register_command(img_path.stem, description="[Image]")(callback)
