import gc
import argparse
import tempfile
import aiohttp
import asyncio
import logging
import vapoursynth
from config import config
from functools import partial
from collections import namedtuple
from handle_messages import private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument

core = vapoursynth.core
core.add_cache = False
core.accept_lowercase = True
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))


Scaler = namedtuple("scaler", "name kernel params descaler")
scalers = [
    Scaler(name="Bilinear", kernel="bilinear", params={}, descaler=core.descale.Debilinear),
    Scaler(name="Bicubic (b=1/3, c=1/3)", kernel="bicubic", params=dict(a1=1 / 3, a2=1 / 3),
           descaler=partial(core.descale.Debicubic, b=1 / 3, c=1 / 3)),
    Scaler(name="Bicubic (b=0.5, c=0)", kernel="bicubic", params=dict(a1=0.5, a2=0),
           descaler=partial(core.descale.Debicubic, b=0.5, c=0)),
    Scaler(name="Bicubic (b=0, c=0.5)", kernel="bicubic", params=dict(a1=0, a2=0.5),
           descaler=partial(core.descale.Debicubic, b=0, c=0.5)),
    Scaler(name="Bicubic (b=1, c=0)", kernel="bicubic", params=dict(a1=1, a2=0),
           descaler=partial(core.descale.Debicubic, b=1, c=0)),
    Scaler(name="Bicubic (b=0, c=1)", kernel="bicubic", params=dict(a1=0, a2=1),
           descaler=partial(core.descale.Debicubic, b=0, c=1)),
    Scaler(name="Bicubic (b=0.2, c=0.5)", kernel="bicubic", params=dict(a1=0.2, a2=0.5),
           descaler=partial(core.descale.Debicubic, b=0.2, c=0.5)),
    Scaler(name="Lanczos (3 Taps)", kernel="lanczos", params=dict(taps=3),
           descaler=partial(core.descale.Delanczos, taps=3)),
    Scaler(name="Lanczos (4 Taps)", kernel="lanczos", params=dict(taps=4),
           descaler=partial(core.descale.Delanczos, taps=4)),
    Scaler(name="Lanczos (5 Taps)", kernel="lanczos", params=dict(taps=5),
           descaler=partial(core.descale.Delanczos, taps=5)),
    Scaler(name="Spline16", kernel="spline16", params={}, descaler=core.descale.Despline16),
    Scaler(name="Spline36", kernel="spline36", params={}, descaler=core.descale.Despline36),
]


class GetNative:
    user_cooldown = set()

    def __init__(self, msg_author, img_url=None, native_height=None, filename=None):
        self.plotScaling = 'log'
        self.ar = None
        self.native_height = native_height
        self.msg_author = msg_author
        self.img_url = img_url
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
        self.ar = src.width / src.height

        matrix_s = '709' if src.format.color_family == vapoursynth.RGB else None
        src_luma32 = core.resize.Point(src, format=vapoursynth.YUV444PS, matrix_s=matrix_s)
        src_luma32 = core.std.ShufflePlanes(src_luma32, 0, vapoursynth.GRAY)
        src_luma32 = core.std.Cache(src_luma32)

        results_bin = {}
        for scaler in scalers:
            error = self.geterror(src_luma32, self.native_height, scaler)
            results_bin[scaler.name] = error

        sorted_results = list(sorted(results_bin.items(), key=lambda x: x[1]))
        best_result = sorted_results[0]
        longest_key = max(map(len, results_bin))

        txt_output = "\n".join(f"{scaler_name:{longest_key}}  {value / best_result[1]:7.1%}  {value:.10f}"
                               for scaler_name, value in sorted_results)

        for scaler in scalers:
            if scaler.name == best_result[0]:
                self.save_images(src, scaler, self.native_height)

        end_text = f"Testing scalers for native height: {self.native_height}\n```{txt_output}```\n" \
                   f"Smallest error achieved by \"{best_result[0]}\" ({best_result[1]:.10f})"

        return False, end_text

    def getw(self, h, only_even=True):
        w = h * self.ar
        w = int(round(w))
        if only_even:
            w = w // 2 * 2

        return w

    def geterror(self, clip, h, scaler):
        down = scaler.descaler(clip, self.getw(h, self.ar), h)
        up = upscale(down, self.getw(clip.height, self.ar), clip.height, scaler)
        smask = core.std.Expr([clip, up], 'x y - abs dup 0.015 > swap 0 ?')
        smask = core.std.CropRel(smask, 5, 5, 5, 5)
        mask = core.std.PlaneStats(smask)

        luma = mask.get_frame(0).props.PlaneStatsAverage
        return luma

    def save_images(self, src_luma32, scaler, h):
        src = src_luma32
        src = scaler.descaler(src, self.getw(h, self.ar), h)
        first_out = imwri.Write(src, 'png', f'{self.path}/{self.filename}_source%d.png')
        first_out.get_frame(0)  # trick vapoursynth into rendering the frame

    async def get_image(self):
        with aiohttp.ClientSession() as sess:
            async with sess.get(self.img_url) as resp:
                if resp.status != 200:
                    return None
                with open(f"{self.path}/{self.filename}", 'wb') as f:
                    f.write(await resp.read())
                return f"{self.path}/{self.filename}"


def upscale(src, width, height, scaler):
    upsizer = getattr(src.resize, scaler.kernel)
    if not upsizer:
        upsizer = partial(src.fmtc.resample, kernel=scaler.kernel, **scaler.params)
    if scaler.kernel == 'bicubic':
        upsizer = partial(upsizer, filter_param_a=scaler.params["a1"], filter_param_b=scaler.params["a2"])
    elif scaler.kernel == 'lanczos':
        upsizer = partial(upsizer, filter_param_a=scaler.params["taps"])

    return upsizer(width, height)


def get_attr(obj, attr, default=None):
    for ele in attr.split('.'):
        obj = getattr(obj, ele, default)
        if obj == default:
            return default
    return obj


def to_float(str_value):
    if set(str_value) - set("0123456789./"):
        raise argparse.ArgumentTypeError("Invalid characters in float parameter")
    try:
        return eval(str_value) if "/" in str_value else float(str_value)
    except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
        raise argparse.ArgumentTypeError("Exception while parsing float") from None


@register_command('getscaler', description='Find the best inverse scaler (mostly anime)')
@add_argument("--native_height", "-nh", dest="native_height", type=int, default=720, help="Approximated native height. Default is 720")
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

    delete_message = await client.send_file(message.channel, config.PICTURE.spam + "tenor_loading.gif")

    kwargs = args.__dict__.copy()
    del kwargs["command"]
    filename = message.attachments[0]["filename"]
    kwargs["img_url"] = message.attachments[0]["url"]
    kwargs["filename"] = message.attachments[0]["filename"]

    msg_author = message.author.id
    get_native = GetNative(msg_author, **kwargs)
    try:
        forbidden_error, best_value = await get_native.run()
    except BaseException as err:
        forbidden_error = True
        best_value = "Error in Getscaler, can't process your picture."
        logging.info(f"Error in Getscaler: {err}")
    gc.collect()

    if not forbidden_error:
        await client.send_file(message.channel, get_native.path + f'/{filename}', content=best_value)
        await client.send_file(message.channel, get_native.path + f'/{filename}_source0.png')
    else:
        await private_msg(message, best_value)

    await delete_user_message(message)
    await delete_user_message(delete_message)
    get_native.tmp_dir.cleanup()
