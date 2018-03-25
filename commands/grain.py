import random
import discord
import gc
import tempfile
import aiohttp
import asyncio
import logging
import vapoursynth
from config import config
from handle_messages import private_msg, delete_user_message
from cmd_manager.decorators import register_command

core = vapoursynth.core
core.add_cache = False
core.accept_lowercase = True
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))


class Grain:
    user_cooldown = set()

    def __init__(self, msg_author, img_url, filename):
        self.img_url = img_url
        self.msg_author = msg_author
        self.filename = filename
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = self.tmp_dir.name

    async def run(self):
        self.user_cooldown.add(self.msg_author)
        asyncio.get_event_loop().call_later(1800, lambda: self.user_cooldown.discard(self.msg_author))

        image = await self.get_image()
        if image is None:
            return True, "Can't load image. Pls try it again later."

        src = imwri.Read(image)
        var = random.randint(100, 2000)
        hcorr = random.uniform(0.0, 1.0)
        vcorr = random.uniform(0.0, 1.0)
        src = core.grain.Add(src, var=var, hcorr=hcorr, vcorr=vcorr)
        first_out = imwri.Write(src, 'png', f'{self.path}/{self.filename}_grain%d.png')
        first_out.get_frame(0)  # trick vapoursynth into rendering the frame

        return False, f"var: {var}, hcorr: {hcorr}, vcorr: {vcorr}"

    async def get_image(self):
        with aiohttp.ClientSession() as sess:
            async with sess.get(self.img_url) as resp:
                if resp.status != 200:
                    return None
                with open(f"{self.path}/{self.filename}", 'wb') as f:
                    f.write(await resp.read())
                return f"{self.path}/{self.filename}"


@register_command('grain', description='Grain.')
async def grain(client, message, args):
    if not message.attachments:
        await delete_user_message(message)
        return await private_msg(message, "Picture as attachment is needed.")
    elif "width" not in message.attachments[0]:
        await delete_user_message(message)
        return await private_msg(message, "Filetype is not allowed!")

    if message.author.id in Grain.user_cooldown:
        await delete_user_message(message)
        return await private_msg(message, "Pls use this command only every 30min.")

    delete_message = await client.send_file(message.channel, config.PICTURE.spam + "tenor_loading.gif")

    img_url = message.attachments[0]["url"]
    filename = message.attachments[0]["filename"]

    msg_author = message.author.id
    gra = Grain(msg_author, img_url, filename)
    try:
        forbidden_error, best_value = await gra.run()
    except BaseException as err:
        forbidden_error = True
        best_value = "Error in Grain, can't process your picture."
        logging.info(f"Error in grain: {err}")
    gc.collect()

    if not forbidden_error:
        try:
            await client.send_file(message.channel, gra.path + f'/{filename}_grain0.png', content=f"Grain <:diGG:302631286118285313>\n{best_value}")
        except discord.HTTPException:
            await client.send_message(message.channel, "Too much grain <:notlikemiya:328621519037005826>")
    else:
        await private_msg(message, best_value)

    await delete_user_message(message)
    await delete_user_message(delete_message)
    gra.tmp_dir.cleanup()
