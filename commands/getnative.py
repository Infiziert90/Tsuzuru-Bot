import gc
import argparse
import tempfile
import aiohttp
import asyncio
import logging
import vapoursynth
from config import config
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot
from functools import partial
from handle_messages import private_msg_file, private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument

core = vapoursynth.core
core.add_cache = False
core.accept_lowercase = True
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))


class GetNative:
    user_cooldown = set()

    def __init__(self, msg_author, img_url=None, filename=None, kernel=None, b=None, c=None, taps=None, ar=None,
                 approx=None, min_h=None, max_h=None):
        self.plotScaling = 'log'
        self.min_h = min_h
        self.max_h = max_h
        self.ar = ar
        self.msg_author = msg_author
        self.img_url = img_url
        self.b = b
        self.c = c
        self.taps = taps
        self.approx = approx
        self.kernel = kernel
        self.txt_output = ""
        self.resolutions = []
        self.filename = filename
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = self.tmp_dir.name

    async def run(self):
        self.user_cooldown.add(self.msg_author)
        asyncio.get_event_loop().call_later(60, lambda: self.user_cooldown.discard(self.msg_author))

        image = await self.get_image()
        if image is None:
            return True, "Can't load image. Pls try it again later."

        src = imwri.Read(image)
        if self.ar is 0:
            self.ar = src.width / src.height

        matrix_s = '709' if src.format.color_family == vapoursynth.RGB else None
        src_luma32 = core.resize.Point(src, format=vapoursynth.YUV444PS, matrix_s=matrix_s)
        src_luma32 = core.std.ShufflePlanes(src_luma32, 0, vapoursynth.GRAY)
        src_luma32 = core.std.Cache(src_luma32)

        # descale each individual frame
        resizer = descale_approx if self.approx else descale_accurate
        clip_list = []
        for h in range(self.min_h, self.max_h + 1):
            clip_list.append(resizer(src_luma32, self.getw(h), h, self.kernel, self.b, self.c, self.taps))
        full_clip = core.std.Splice(clip_list, mismatch=True)
        full_clip = upscale(full_clip, self.getw(src.height), src.height, self.kernel, self.b, self.c, self.taps)
        if self.ar != src.width / src.height:
            src_luma32 = upscale(src_luma32, self.getw(src.height), src.height, self.kernel, self.b, self.c, self.taps)
        expr_full = core.std.Expr([src_luma32 * full_clip.num_frames, full_clip], 'x y - abs dup 0.015 > swap 0 ?')
        full_clip = core.std.CropRel(expr_full, 5, 5, 5, 5)
        full_clip = core.std.PlaneStats(full_clip)
        full_clip = core.std.Cache(full_clip)

        tasks_pending = set()
        futures = {}
        vals = []
        for frame_index in range(len(full_clip)):
            fut = asyncio.ensure_future(asyncio.wrap_future(full_clip.get_frame_async(frame_index)))
            tasks_pending.add(fut)
            futures[fut] = frame_index
            while len(tasks_pending) >= core.num_threads * (2 if self.approx else 1) + 2:
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

        return False, best_value

    def getw(self, h, only_even=True):
        w = h * self.ar
        w = int(round(w))
        if only_even:
            w = w // 2 * 2

        return w

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

        bicubic_params = self.kernel == 'bicubic' and f'Scaling parameters:\nb = {self.b:.2f}\nc = {self.c:.2f}\n' or ''
        best_values = f"{'p, '.join([str(r + self.min_h) for r in self.resolutions])}p"
        self.txt_output += f"Resize Kernel: {self.kernel}\n{bicubic_params}Native resolution(s) (best guess): " \
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

    async def get_image(self):
        with aiohttp.ClientSession() as sess:
            async with sess.get(self.img_url) as resp:
                if resp.status != 200:
                    return None
                with open(f"{self.path}/{self.filename}", 'wb') as f:
                    f.write(await resp.read())
                return f"{self.path}/{self.filename}"


def upscale(src, width, height, kernel, b, c, taps):
    resizer = getattr(src.resize, kernel.title())
    if not resizer:
        return src.fmtc.resample(width, height, kernel=kernel, a1=b, a2=c, taps=taps)
    if kernel == 'bicubic':
        resizer = partial(resizer, filter_param_a=b, filter_param_b=c)
    elif kernel == 'lanczos':
        resizer = partial(resizer, filter_param_a=taps)

    return resizer(width, height)


def descale_accurate(src, width, height, kernel, b, c, taps):
    descale = getattr(src, 'descale_getnative', None)
    if descale is None:
        descale = getattr(src, 'descale')
    descale = getattr(descale, 'De' + kernel)
    if kernel == 'bicubic':
        descale = partial(descale, b=b, c=c)
    elif kernel == 'lanczos':
        descale = partial(descale, taps=taps)

    return descale(width, height)


def descale_approx(src, width, height, kernel, b, c, taps):
    return src.fmtc.resample(width, height, kernel=kernel, taps=taps, a1=b, a2=c, invks=True, invkstaps=taps)


def to_float(str_value):
    if set(str_value) - set("0123456789./"):
        raise argparse.ArgumentTypeError("Invalid characters in float parameter")
    try:
        return eval(str_value) if "/" in str_value else float(str_value)
    except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
        raise argparse.ArgumentTypeError("Exception while parsing float") from None


@register_command('getnative', description='Find the native resolution(s) of upscaled material (mostly anime)')
@add_argument('--kernel', '-k', dest='kernel', type=str.lower, default='bilinear', help='Resize kernel to be used')
@add_argument('--bicubic-b', '-b', dest='b', type=to_float, default="1/3", help='B parameter of bicubic resize')
@add_argument('--bicubic-c', '-c', dest='c', type=to_float, default="1/3", help='C parameter of bicubic resize')
@add_argument('--lanczos-taps', '-t', dest='taps', type=int, default=3, help='Taps parameter of lanczos resize')
@add_argument('--aspect-ratio', '-ar', dest='ar', type=to_float, default=0, help='Force aspect ratio. Only useful for anamorphic input')
@add_argument('--approx', '-ap', dest="approx", action="store_true", help='Use fmtc instead of descale [faster, loss of accuracy]')
@add_argument('--min-height', '-min', dest="min_h", type=int, default=500, help='Minimum height to consider')
@add_argument('--max-heigth', '-max', dest="max_h", type=int, default=1000, help='Maximum height to consider [max 1080 atm]')
async def getnative(client, message, args):
    if not message.attachments:
        await delete_user_message(message)
        return await private_msg(message, "Picture as attachment is needed.")
    elif "width" not in message.attachments[0]:
        await delete_user_message(message)
        return await private_msg(message, "Filetype is not allowed!")

    if message.author.id in GetNative.user_cooldown:
        await delete_user_message(message)
        return await private_msg(message, "Pls use this command only every 1min.")

    width = message.attachments[0]["width"]
    height = message.attachments[0]["height"]
    if width * height > 8300000:
        await delete_user_message(message)
        return await private_msg(message, "Picture is too big.")
    elif args.min_h >= height:
        return await private_msg(message, f"Picture is to small or equal for min height {args.min_h}.")
    elif args.min_h >= args.max_h:
        return await private_msg(message, f"Your min height is bigger or equal to max height.")
    elif args.max_h - args.min_h > 1000:
        return await private_msg(message, f"Max - min height bigger than 1000 is not allowed")
    elif args.max_h > height:
        await private_msg(message, f"Your max height cant be bigger than your image dimensions. New max height is {height}")
        args.max_h = height

    if args.approx:
        try:
            core.fmtc.resample(core.std.BlankClip(), kernel=args.kernel)
        except vapoursynth.Error:
            return await private_msg(message, 'fmtc: Invalid kernel specified.')
    else:
        if args.kernel not in ['spline36', 'spline16', 'lanczos', 'bicubic', 'bilinear']:
            return await private_msg(message, f'descale: {args.kernel} is not a supported kernel. Try -ap for approximation.')

    delete_message = await client.send_file(message.channel, config.PICTURE.spam + "tenor_loading.gif")

    kwargs = args.__dict__.copy()
    del kwargs["command"]
    img_url = message.attachments[0]["url"]
    filename = message.attachments[0]["filename"]
    kwargs["img_url"] = img_url
    kwargs["filename"] = filename

    msg_author = message.author.id
    getnative = GetNative(msg_author, **kwargs)
    try:
        forbidden_error, best_value = await getnative.run()
    except BaseException as err:
        forbidden_error = True
        best_value = "Error in Getnative, can't process your picture."
        logging.info(f"Error in getnative: {err}")
    gc.collect()

    if not forbidden_error:
        content = ''.join([
        f"\nKernel: {getnative.kernel} ",
        f"AR: {getnative.ar:.2f} ",
        f"B: {getnative.b:.2f} C: {getnative.c:.2f} " if getnative.kernel == "bicubic" else "",
        f"Taps: {getnative.taps} " if getnative.kernel == "lanczos" else "",
        f"\n{best_value}",
        f"\n[approximation]" if getnative.approx else "",
        ])
        await private_msg_file(message, f"{getnative.path}/{filename}.txt", "Output from getnative.")
        await client.send_file(message.channel, getnative.path + f'/{filename}.png', content=content)
    else:
        await private_msg(message, best_value)

    await delete_user_message(delete_message)
    getnative.tmp_dir.cleanup()
