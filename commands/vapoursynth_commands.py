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
import inspect
import argparse
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
from config import config
from utils import get_file
from functools import partial
from discord import File, HTTPException
from cmd_manager.decorators import register_command, add_argument
from handle_messages import private_msg, delete_user_message

core = vapoursynth.core
core.add_cache = False
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))
lossy = ["jpg", "jpeg", "gif"]


def get_upscaler(kernel=None, b=None, c=None, taps=None):
    upsizer = getattr(core.resize, kernel.title())
    if kernel == 'bicubic':
        upsizer = partial(upsizer, filter_param_a=b, filter_param_b=c)
    elif kernel == 'lanczos':
        upsizer = partial(upsizer, filter_param_a=taps)

    return upsizer


def get_descaler(kernel=None, b=None, c=None, taps=None):
    descale = getattr(core, "descale_getnative", None)
    if descale is None:
        logging.warning("Only the slow descale is installed or you did not change the namespace.")
        descale = getattr(core, "descale")
    descale = getattr(descale, 'De' + kernel)
    if kernel == 'bicubic':
        descale = partial(descale, b=b, c=c)
    elif kernel == 'lanczos':
        descale = partial(descale, taps=taps)

    return descale


class DefineScaler:
    def __init__(self, kernel, b=None, c=None, taps=None):
        self.kernel = kernel
        self.b = b
        self.c = c
        self.taps = taps
        self.descaler = get_descaler(kernel=kernel, b=b, c=c, taps=taps)
        self.upscaler = get_upscaler(kernel=kernel, b=b, c=c, taps=taps)


class Getnative:
    user_cooldown = set()

    def __init__(self, mes, spam, img_url, fn, scaler, min_h, max_h):
        self.mes = mes
        self.spam = spam
        self.img_url = img_url
        self.filename = fn
        self.scaler = scaler
        self.min_h = min_h
        self.max_h = max_h
        self.plotScaling = 'log'
        self.txt_output = ""
        self.resolutions = []
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = self.tmp_dir.name

    async def run(self):
        src = await set_cooldown_and_get_image(self)
        ar = src.width / src.height
        src_luma32 = convert_rgb_gray32(src)
        full_clip = self.compute_error(src_luma32, ar)

        tasks_pending = set()
        futures = {}
        vals = []
        for frame_index in range(len(full_clip)):
            fut = asyncio.ensure_future(asyncio.wrap_future(full_clip.get_frame_async(frame_index)))
            tasks_pending.add(fut)
            futures[fut] = frame_index
            while len(tasks_pending) >= core.num_threads / 2:  # let the bot not use 100% of the cpu
                tasks_done, tasks_pending = await asyncio.wait(
                    tasks_pending, return_when=asyncio.FIRST_COMPLETED)
                vals += [(futures.pop(task), task.result().props.PlaneStatsAverage) for task in tasks_done]

        tasks_done, _ = await asyncio.wait(tasks_pending)
        vals += [(futures.pop(task), task.result().props.PlaneStatsAverage) for task in tasks_done]
        vals = [v for _, v in sorted(vals)]
        ratios, vals, best_value = self.analyze_results(vals)
        self.save_plot(vals)
        self.txt_output += 'Raw data:\nResolution\t | Relative Error\t | Relative difference from last\n'
        for i, error in enumerate(vals):
            self.txt_output += f'{i + self.min_h:4d}\t\t | {error:.10f}\t\t\t | {ratios[i]:.2f}\n'

        with open(f"{self.path}/{self.filename}.txt", "w") as file_open:
            file_open.writelines(self.txt_output)

        return best_value

    def compute_error(self, clip, ar):
        down = self.scaler.descaler
        up = self.scaler.upscaler
        clip_list = []
        for h in range(self.min_h, self.max_h + 1):
            clip_list.append(down(clip, getw(ar, h), h))
        full_clip = core.std.Splice(clip_list, mismatch=True)
        full_clip = up(full_clip, getw(ar, clip.height), clip.height)
        expr_full = core.std.Expr([clip * full_clip.num_frames, full_clip], 'x y - abs dup 0.015 > swap 0 ?')
        full_clip = core.std.CropRel(expr_full, 5, 5, 5, 5)
        full_clip = core.std.PlaneStats(full_clip)
        return core.std.Cache(full_clip)

    def analyze_results(self, vals):
        ratios = [0.0]
        for i in range(1, len(vals)):
            last = vals[i - 1]
            current = vals[i]
            ratios.append(current and last / current)
        sorted_array = sorted(ratios, reverse=True)  # make a copy of the array because we need the unsorted array later
        max_difference = sorted_array[0]

        differences = [s for s in sorted_array if s - 1 > (max_difference - 1) * 0.33][:5]

        for diff in differences:
            current = ratios.index(diff)
            # don't allow results within 20px of each other
            for res in self.resolutions:
                if res - 20 < current < res + 20:
                    break
            else:
                self.resolutions.append(current)

        scaler = self.scaler
        bicubic_params = scaler.kernel == 'bicubic' and f'Parameters:\nb= {scaler.b:.2f}\nc={scaler.c:.2f}\n' or ''
        best_values = f"{'p, '.join([str(r + self.min_h) for r in self.resolutions])}p"
        self.txt_output += f"Resize Kernel: {scaler.kernel}\n{bicubic_params}Native resolution(s) (best guess): " \
                           f"{best_values}\nPlease check the graph manually for more accurate results\n\n"

        return ratios, vals, f"Native resolution(s) (best guess): {best_values}"

    def save_plot(self, vals):
        matplotlib.pyplot.style.use('dark_background')
        matplotlib.pyplot.plot(range(self.min_h, self.max_h + 1), vals, '.w-')
        matplotlib.pyplot.title(self.filename)
        matplotlib.pyplot.ylabel('Relative error')
        matplotlib.pyplot.xlabel('Resolution')
        matplotlib.pyplot.yscale(self.plotScaling)
        matplotlib.pyplot.savefig(f'{self.path}/{self.filename}.png')
        matplotlib.pyplot.clf()


class Grain:
    user_cooldown = set()

    def __init__(self, mes, spam, img_url, filename):
        self.mes = mes
        self.spam = spam
        self.img_url = img_url
        self.filename = filename
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = self.tmp_dir.name

    async def run(self):
        src = await set_cooldown_and_get_image(self)
        var = random.randint(1000, 20000)
        hcorr = random.uniform(0.3, 1.0)
        vcorr = random.uniform(0.3, 1.0)
        src = core.grain.Add(src, var=var, hcorr=hcorr, vcorr=vcorr)
        first_out = imwri.Write(src, 'png', f'{self.path}/{self.filename}_grain%d.png')
        first_out.get_frame(0)  # trick vapoursynth into rendering the frame

        return f"var: {var}, hcorr: {hcorr}, vcorr: {vcorr}"


async def set_cooldown_and_get_image(self):
    self.user_cooldown.add(self.mes.author.id)
    asyncio.get_event_loop().call_later(120, lambda: self.user_cooldown.discard(self.mes.author.id))

    image = await get_file(self.img_url, self.path, self.filename)
    if image is None:
        raise BaseException("Can't load image. Please try it again later.")

    return imwri.Read(image, float_output=True)


def convert_rgb_gray32(src):
    matrix_s = '709' if src.format.color_family == vapoursynth.RGB else None
    src_luma32 = core.resize.Point(src, format=vapoursynth.YUV444PS, matrix_s=matrix_s)
    src_luma32 = core.std.ShufflePlanes(src_luma32, 0, vapoursynth.GRAY)
    src_luma32 = core.std.Cache(src_luma32)
    return src_luma32


def getw(ar, h, only_even=True):
    w = h * ar
    w = int(round(w))
    if only_even:
        w = w // 2 * 2

    return w


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


async def error_handler(cls, func_name, err):
    logging.info(f"Error in {func_name}: {err}")
    await private_msg(cls.mes, f"Error in {func_name}: ```{err}```")
    return await cleanup(cls)


async def cleanup(cls):
    await delete_user_message(cls.mes)
    await delete_user_message(cls.spam)
    cls.tmp_dir.cleanup()


@register_command(description='Find the native resolution(s) of upscaled material')
@add_argument('--min-height', '-min', dest="min_h", type=int, default=500, help='Min height to consider')
@add_argument('--max-height', '-max', dest="max_h", type=int, default=1000, help='Max height to consider [max 1080]')
@add_argument('--kernel', '-k', dest='kernel', type=str.lower, default="bicubic", help='Resize kernel to be used')
@add_argument('--bicubic-b', '-b', dest='b', type=to_float, default="1/3", help='B parameter of bicubic resize')
@add_argument('--bicubic-c', '-c', dest='c', type=to_float, default="1/3", help='C parameter of bicubic resize')
@add_argument('--lanczos-taps', '-t', dest='taps', type=int, default=3, help='Taps parameter of lanczos resize')
async def getnative(client, message, args):
    if not await check_message(message):
        return

    if message.author.id in Getnative.user_cooldown:
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

    if args.kernel not in ['spline36', 'spline16', 'lanczos', 'bicubic', 'bilinear']:
        return await private_msg(message, f'descale: {args.kernel} is not a supported kernel.')
    scaler = DefineScaler(args.kernel, b=args.b, c=args.c, taps=args.taps)

    delete_message = await message.channel.send(file=File(config.PICTURE.spam + "tenor_loading.gif"))

    img_url = message.attachments[0].url
    filename = message.attachments[0].filename
    getn = Getnative(message, delete_message, img_url, filename, scaler, args.min_h, args.max_h)
    try:
        import time
        start = time.time()
        best_value = await getn.run()
        logging.info(time.time() - start)
    except BaseException as err:
        return await error_handler(getn, inspect.currentframe().f_code.co_name, err)

    gc.collect()
    content = ''.join([
        f"Output:"
        f"\nKernel: {scaler.kernel} ",
        f"B: {scaler.b:.2f} C: {scaler.c:.2f} " if scaler.kernel == "bicubic" else "",
        f"Taps: {scaler.taps} " if scaler.kernel == "lanczos" else "",
        f"\n{best_value}",
    ])
    await private_msg(message, content="Output from getnative.", file=File(f"{getn.path}/{filename}.txt"))
    await message.channel.send(content=f"Input\n{message.author}: '{message.content}'", file=File(f'{getn.path}/{filename}'))
    await message.channel.send(content=content, file=File(f'{getn.path}/{filename}.png'))
    await cleanup(getn)


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
    gra = Grain(message, delete_message, img_url, filename)
    try:
        best_value = await gra.run()
    except BaseException as err:
        return await error_handler(gra, inspect.currentframe().f_code.co_name, err)

    gc.collect()
    try:
        await message.channel.send(file=File(f'{gra.path}/{filename}_grain0.png'),
                                   content=f"Grain <:diGG:302631286118285313>\n{best_value}")
    except HTTPException:
        await message.channel.send("Too much grain <:notlikemiya:328621519037005826>")
    await cleanup(gra)
