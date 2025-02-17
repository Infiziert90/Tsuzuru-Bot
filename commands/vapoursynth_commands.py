import logging
from utils import HelperException
try:
    import vapoursynth
except ImportError:
    raise HelperException("VapourSynth is not available for the bot, dropping VapourSynth commands.")
except Exception as err:
    logging.warning(err)
    raise HelperException("VapourSynth is broken, dropping VapourSynth commands.")

import gc
import os
import random
import asyncio
import aiohttp
import inspect
import argparse
import tempfile
import getnative.app
from config import config
from utils import get_file
from discord import File, HTTPException
from cmd_manager.decorators import register_command, add_argument
from handle_messages import private_msg, delete_user_message

core = vapoursynth.core
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))
lossy = ["jpg", "jpeg", "gif"]
user_cooldown = set()


class Grain:
    user_cooldown = set()

    def __init__(self, filename, src, path):
        self.filename = filename
        self.path = path
        self.src = src

    async def run(self):
        used = {
            "var": [],
            "hcorr": [],
            "vcorr": [],
        }

        for _ in range(random.randint(1, 3)):
            await asyncio.sleep(0.2)  # give the bot event time

            used["var"].append(random.randint(10, 1000))
            used["hcorr"].append(random.uniform(0.1, 1.0))
            used["vcorr"].append(random.uniform(0.1, 1.0))
            self.src = core.grain.Add(self.src, var=used["var"][-1], hcorr=used["hcorr"][-1], vcorr=used["vcorr"][-1])
        first_out = imwri.Write(self.src, 'png', f'{self.path}/{self.filename}_grain%d.png')
        first_out.get_frame(0)  # trick vapoursynth into rendering the frame

        return f"var: {used['var']}\nhcorr: {used['hcorr']}\nvcorr: {used['vcorr']}"


def to_float(str_value):
    if set(str_value) - set("0123456789./"):
        raise argparse.ArgumentTypeError("Invalid characters in float parameter")
    try:
        return eval(str_value) if "/" in str_value else float(str_value)
    except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
        raise argparse.ArgumentTypeError("Exception while parsing float") from None


async def check_message(message):
    if not message.attachments:
        await private_msg(message, "Picture as attachment is needed.")
    elif not message.attachments[0].width:
        await private_msg(message, "Filetype is not allowed!")
    elif message.attachments[0].width * message.attachments[0].height > 8300000:
        await private_msg(message, "Picture is too big.")
    else:
        return True

    await delete_user_message(message)
    return False


async def error_handler(mes, spam, tmp_dir, func_name, err):
    logging.info(f"Error in {func_name}: {err}")
    await private_msg(mes, f"Error in {func_name}: ```{err}```")
    return await cleanup(mes, spam, tmp_dir)


async def cleanup(mes, spam, tmp_dir):
    await delete_user_message(mes)
    await delete_user_message(spam)
    tmp_dir.cleanup()


async def set_cooldown(user_id):
    user_cooldown.add(user_id)
    asyncio.get_event_loop().call_later(120, lambda: user_cooldown.discard(user_id))


async def get_image_as_videonode(img_url, path, filename):
    image = await get_file(img_url, path, filename)
    if image is None:
        raise BaseException("Can't load image. Please try it again later.")

    return imwri.Read(image, float_output=True)


@register_command(name="getnative", description='Find the native resolution(s) of upscaled material')
@add_argument('--min-height', '-min', dest="min_h", type=int, default=500, help='Min height to consider')
@add_argument('--max-height', '-max', dest="max_h", type=int, default=1000, help='Max height to consider [max 1080]')
@add_argument('--aspect-ratio', '-ar', dest='ar', type=to_float, default=0, help='Force aspect ratio. Only useful for anamorphic input')
@add_argument('--kernel', '-k', dest='kernel', type=str.lower, default="bicubic", help='Resize kernel to be used')
@add_argument('--bicubic-b', '-b', dest='b', type=to_float, default="1/3", help='B parameter of bicubic resize')
@add_argument('--bicubic-c', '-c', dest='c', type=to_float, default="1/3", help='C parameter of bicubic resize')
@add_argument('--stepping', '-steps', dest='steps', type=int, default=1, help='This changes the way getnative will handle resolutions. Example steps=3 [500p, 503p, 506p ...]')
@add_argument('--lanczos-taps', '-t', dest='taps', type=int, default=3, help='Taps parameter of lanczos resize')
async def getnative_command(client, message, args):
    if not await check_message(message):
        return

    if message.author.id in user_cooldown:
        await delete_user_message(message)
        return await private_msg(message, "Cooldown active. Try again in two minutes.")
    elif os.path.splitext(message.attachments[0].filename)[1][1:] in lossy:
        await message.channel.send(file=File(config.PICTURE.spam + "lossy.png"))
        return await private_msg(message, f"Don't use lossy formats. Lossy formats are:\n{', '.join(lossy)}")
    elif args.min_h >= message.attachments[0].height:
        return await private_msg(message, f"Picture is to small for {args.min_h} min height.")
    elif args.min_h >= args.max_h:
        return await private_msg(message, f"Your min height is bigger or equal to max height.")
    elif args.max_h - args.min_h > 1000:
        return await private_msg(message, f"Max - min height is over 1000.")
    elif args.max_h > message.attachments[0].height:
        await private_msg(message, f"Your max height can't be bigger than your image dimensions. "
                                   f"New max height is {message.attachments[0].height}")
        args.max_h = message.attachments[0].height

    delete_message = await message.channel.send(file=File(config.PICTURE.spam + "tenor_loading.gif"))

    img_url = message.attachments[0].url
    filename = message.attachments[0].filename

    tmp_dir = tempfile.TemporaryDirectory()
    path = tmp_dir.name

    largs = [
        '--min-height', str(args.min_h),
        '--max-height', str(args.max_h),
        '--aspect-ratio', str(args.ar),
        '--kernel', str(args.kernel),
        '--bicubic-b', str(args.b),
        '--bicubic-c', str(args.c),
        '--lanczos-taps', str(args.taps),
        '--stepping', str(args.steps),
        '--output-dir', str(path),
        '--plot-format', 'png',
    ]

    await set_cooldown(message.author.id)
    img = await get_image_as_videonode(img_url, path, filename)

    try:
        import time
        start = time.time()
        best_value, _, getn = await getnative.app.getnative(largs, img, scaler=None)
        logging.info(time.time() - start)
    except BaseException as err:
        return await error_handler(message, delete_message, tmp_dir, inspect.currentframe().f_code.co_name, err)

    gc.collect()
    content = ''.join([
        f"Output:"
        f"\n{getn.scaler}",
        f"\n{best_value}",
    ])
    await private_msg(message, content="Output from getnative.", file=File(f"{getn.output_dir}/{getn.filename}.txt"))
    await message.channel.send(content=f"Input\n{message.author}: '{message.content}'", file=File(f'{path}/{filename}'))
    await message.channel.send(content=content, file=File(f'{getn.output_dir}/{getn.filename}.png'))
    await cleanup(message, delete_message, tmp_dir)


@register_command(description='Grain.')
async def grain(client, message, args):
    if not await check_message(message):
        return

    if message.author.id in Grain.user_cooldown:
        await delete_user_message(message)
        return await private_msg(message, "Please only use this command once every 2 minutes.")

    delete_message = await message.channel.send(file=File(config.PICTURE.spam + "tenor_loading.gif"))

    img_url = message.attachments[0].url
    filename = message.attachments[0].filename
    tmp_dir = tempfile.TemporaryDirectory()
    path = tmp_dir.name

    await set_cooldown(message.author.id)
    img = await get_image_as_videonode(img_url, path, filename)

    gra = Grain(filename, img, path)
    try:
        best_value = await gra.run()
    except BaseException as err:
        return await error_handler(message, delete_message, tmp_dir, inspect.currentframe().f_code.co_name, err)

    gc.collect()
    try:
        await message.channel.send(file=File(f'{path}/{filename}_grain0.png'), content=f"Grain <:diGG:302631286118285313>\n{best_value}")
    except HTTPException:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://0x0.st/') as resp:
                if resp.ok:
                    final_resp = await session.post('https://0x0.st/', data={'file': open(f'{path}/{filename}_grain0.png', 'rb')})
                    if final_resp.ok:
                        await message.channel.send(content=f"Grain <:diGG:302631286118285313>\n{best_value}\n{final_resp.content.read_nowait().decode('utf-8')}")
                    else:
                        await message.channel.send("Too much grain <:notlikemiya:328621519037005826>")
    await cleanup(message, delete_message, tmp_dir)
