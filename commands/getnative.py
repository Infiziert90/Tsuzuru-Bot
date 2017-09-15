import gc
import argparse
import tempfile
import aiohttp
import asyncio
import vapoursynth
from config import config
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot
import fvsfunc_getnative as fvs
from handle_messages import private_msg_file, private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument

core = vapoursynth.core
core.add_cache = False
imwri = core.imwri if hasattr(core, 'imwri') else core.imwrif


class GetNative:
    user_cooldown = set()

    def __init__(self, msg_author, img_url=None, filename=None, kernel=None, b=None, c=None, taps=None, ar=None, approx=None):
        self.minHeight = 500
        self.maxHeight = 1080
        self.plotScaling = 'log'
        self.ar = ar
        self.msg_author = msg_author
        self.img_url = img_url
        self.b = b
        self.c = c
        self.taps = taps
        self.approx = approx
        self.kernel = kernel
        self.txtOutput = ""
        self.filename = filename
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = self.tmp_dir.name

    async def run(self):
        self.user_cooldown.add(self.msg_author)
        asyncio.get_event_loop().call_later(60, lambda: self.user_cooldown.discard(self.msg_author))

        if not self.approx and self.kernel not in ['spline36', 'spline16', 'lanczos', 'bicubic', 'bilinear']:
            return True, f'descale: kernel {self.kernel} only supports approximation.'

        try:
            clip = core.std.BlankClip()
            core.fmtc.resample(clip, kernel=self.kernel)
        except vapoursynth.Error:
            return True, "fmtc: Invalid kernel specified."

        image = await self.get_image()
        if image is None:
            return True, "Can't load image. Pls try it again later."

        src = imwri.Read(image)
        if src.height < self.maxHeight:
            self.maxHeight = src.height

        if src.height < self.minHeight:
            self.minHeight = 100

        if self.ar is 0:
            self.ar = src.width / src.height

        src_luma32 = core.resize.Point(src, format=vapoursynth.YUV444PS, matrix_s="709")
        src_luma32 = core.std.ShufflePlanes(src_luma32, 0, vapoursynth.GRAY)
        src_luma32 = core.std.Cache(src_luma32)

        # descale each individual frame
        resizer = core.fmtc.resample if self.approx else fvs.Resize
        clip_list = []
        for h in range(self.minHeight, self.maxHeight + 1):
            clip_list.append(resizer(src_luma32, self.getw(h), h, kernel=self.kernel, a1=self.b, a2=self.c, invks=True,
                                     taps=self.taps))
        full_clip = core.std.Splice(clip_list, mismatch=True)
        full_clip = fvs.Resize(full_clip, self.getw(src.height), src.height, kernel=self.kernel, a1=self.b, a2=self.c,
                               taps=self.taps)
        if self.ar != src.width / src.height:
            src_luma32 = resizer(src_luma32, self.getw(src.height), src.height, kernel=self.kernel,
                                 a1=self.b, a2=self.c, taps=self.taps)
        full_clip = core.std.Expr([src_luma32 * full_clip.num_frames, full_clip], 'x y - abs dup 0.015 > swap 0 ?')
        full_clip = core.std.CropRel(full_clip, 5, 5, 5, 5)
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
        self.txtOutput += 'Raw data:\nResolution\t | Relative Error\t | Relative difference from last\n'
        for i, error in enumerate(vals):
            self.txtOutput += f'{i + self.minHeight:4d}\t\t | {error:.6f}\t\t\t | {ratios[i]:.2f}\n'

        with open(f"{self.path}/{self.filename}.txt", "w") as file_open:
            file_open.writelines(self.txtOutput)

        return False, best_value

    def getw(self, h, only_even=True):
        w = h * self.ar
        w = int(round(w))
        if only_even:
            w = w // 2 * 2
        return w

    def analyze_results(self, vals):
        ratios = [0.0]
        resolutions = []
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
            for res in resolutions:
                if res - 20 < current < res + 20:
                    break
            else:
                resolutions.append(current)
        bicubic_params = self.kernel == 'bicubic' and f'Scaling parameters:\nb = {self.b:.2f}\nc = {self.c:.2f}\n' or ''
        best_values = f"{'p, '.join([str(r + self.minHeight) for r in resolutions])}p"
        self.txtOutput += f"Resize Kernel: {self.kernel}\n{bicubic_params}Native resolution(s) (best guess): " \
                          f"{best_values}\nPlease check the graph manually for more accurate results\n\n"

        return ratios, vals, f"Native resolution(s) (best guess): {best_values}"

    def save_plot(self, vals):
        matplotlib.pyplot.style.use('dark_background')
        matplotlib.pyplot.plot(range(self.minHeight, self.maxHeight + 1), vals, '.w-')
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


def to_float(str_value):
    if set(str_value) - set("0123456789./"):
        raise argparse.ArgumentTypeError("Invalid characters in float parameter")
    try:
        return eval(str_value) if "/" in str_value else float(str_value)
    except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
        raise argparse.ArgumentTypeError("Exception while parsing float") from None


@register_command('getnative', is_enabled=None,
                  description='Find the native resolution(s) of upscaled material (mostly anime)')
@add_argument('--kernel', '-k', dest='kernel', type=str.lower, default='bilinear', help='Resize kernel to be used')
@add_argument('--bicubic-b', '-b', dest='b', type=to_float, default="1/3", help='B parameter of bicubic resize')
@add_argument('--bicubic-c', '-c', dest='c', type=to_float, default="1/3", help='C parameter of bicubic resize')
@add_argument('--lanczos-taps', '-t', dest='taps', type=int, default=3, help='Taps parameter of lanczos resize')
@add_argument('--aspect-ratio', '-a', dest='ar', type=to_float, default=0, help='Force aspect ratio. Only useful for'
                                                                                ' anamorphic input')
@add_argument('--no-approx', '-no-ap', dest="approx", action="store_false", help='Use descale instead of fmtc for'
                                                                                 ' better accuracy [really slow]')
async def getnative(client, message, args):
    if not message.attachments:
        return await private_msg(message, "Picture as attachment is needed.")
    elif "width" not in message.attachments[0]:
        return await private_msg(message, "Filetype is not allowed!")

    if message.attachments[0]["width"] * message.attachments[0]["height"] > 8300000:
        return await private_msg(message, "Picture is too big.")
    elif not (message.attachments[0]["height"] > 100 and message.attachments[0]["width"] > 100):
        return await private_msg(message, "Picture is too small.")

    if message.author.id in GetNative.user_cooldown:
        return await private_msg(message, "Pls use this command only every 1min.")

    delete_message = await client.send_file(message.channel, config.PICTURE.spam + "tenor_loading.gif")

    kwargs = args.__dict__.copy()
    del kwargs["command"]
    img_url = message.attachments[0]["url"]
    filename = message.attachments[0]["filename"]
    kwargs["img_url"] = img_url
    kwargs["filename"] = filename

    msg_author = message.author.id
    get_native = GetNative(msg_author, **kwargs)
    forbidden_error, best_value = await get_native.run()
    gc.collect()

    if not forbidden_error:
        content = ''.join([
            f"<@!{msg_author}>",
            f"\nKernel: {args.kernel} ",
            f"B: {args.b:.2f} C: {args.c:.2f} " if args.kernel == "bicubic" else "",
            f"AR: {args.ar} " if args.ar else "",
            f"Taps: {args.taps} " if args.kernel == "lanczos" else "",
            f"\n{best_value}",
            f"\n[approximation]" if args.approx else "",
        ])
        await private_msg_file(message, f"{get_native.path}/{filename}.txt", "Output from getnative.")
        await client.send_file(message.channel, get_native.path + f'/{filename}', content=content)
        await client.send_file(message.channel, get_native.path + f'/{filename}.png')
    else:
        await private_msg(message, best_value)

    await delete_user_message(message)
    await delete_user_message(delete_message)
    get_native.tmp_dir.cleanup()
