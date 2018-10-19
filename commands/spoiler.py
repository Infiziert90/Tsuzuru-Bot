import math
import re
import utils
import discord
import tempfile
import itertools
import subprocess
from config import config
from handle_messages import private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument, add_group

tmp_path_dir = tempfile.TemporaryDirectory()
tmp_path = tmp_path_dir.name
FONT_PATH = config.MAIN.font
CHAR_WIDTH = 30.24  # for OpenSans 55 (value+2)
CHAR_HEIGHT = 62  # for OpenSans 55
TEST_WIDTH = 1920
RATIO = 1.35  # 1920x1420
PADDING = 50

ffmpeg_generate_height = """-loglevel error
-f lavfi
-i color=c=black:s=2x2:d=0.06
-vf drawtext=\
fontsize=55\
:fontfile={font}\
:text='%{{eif\\:print(th,16)\\:}}{user_text}\
:x={pad}:y={pad}'
-f null
-""".replace("\n", " ")

ffmpeg_output_cmd = """-loglevel error
-y
-f lavfi
-i color=c=black:s={width}x{height}:d=3
-vf drawtext=\
enable='between(t,0,0.5)'\
:fontfile={font}\
:text='{user_header}'\
:fontcolor=white\
:fontsize=55\
:x=(w-tw)/2\
:y=(h/3)\
,drawtext=\
fontsize=55\
:enable='between(t,0.501,3)'\
:fontfile={font}\
:text='{user_text}'\
:fontcolor=white\
:x={pad}:y={pad}
-r 2
{out_path}/spoiler.webm""".replace("\n", " ")

ffmpeg_image_cmd = """-loglevel error
-y
-f lavfi
-i color=c=black:s={width}x{height}:d=3
-i {image}
-filter_complex drawtext=\
enable='between(t,0,0.5)'\
:fontfile={font}\
:text='{user_header}'\
:fontcolor=white\
:fontsize=55\
:x=(w-tw)/2\
:y=(h/3)\
,[1:v]overlay=0:0\
:enable='between(t,0,0)'
-r 2
{out_path}/spoiler.webm""".replace("\n", " ")


class ImageFailed(BaseException):
    pass


def replace_chars(text):
    text = text.replace("  ", " ")
    text = text.replace("„", "“")
    text = text.replace("‒", "-")
    text = text.replace("\"", "“")
    text = text.replace(":", "\\\\\\:")
    text = text.replace("=", "\\\\\\=")
    text = text.replace("$", "\\\\\\$")
    text = text.replace("`", "\\\\\\`")
    text = text.replace("{", "\\\\\\{")
    text = text.replace("}", "\\\\\\}")
    text = text.replace("%", "\\\\\\%")
    text = text.replace("§", "\\\\\\§")

    return text


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def split_spoiler_lines(text, max_width):
    lines = []
    for source_line in text.splitlines():
        tokens = re.split(r"([^\w']+)", source_line)
        cur_line = ""
        for word, sep in grouper(tokens, 2, ''):
            if len(cur_line) + len(word) + len(sep) > max_width:
                lines.append(cur_line.strip())
                cur_line = word + sep
            else:
                cur_line += word + sep

        lines.append(cur_line)

    return '\n'.join(lines)


# h=CHAR_HEIGHT
def dimensions(s, p=PADDING, h=0, r=RATIO):
    # determine dimensions
    #   surface=x*y; x=ratio*y
    #     height = int(math.sqrt(surface / RATIO))
    #     width = int(RATIO * height)
    # with padding
    #   surface=(x-pad*2)*(y-pad*2); x=ratio*y
    # with safety offset of one line
    #   surface=(x-pad*2-char_height)*(y-pad*2); x=ratio*y
    #   s=(ry-2p-h)*(y-2p)
    #   https://www.wolframalpha.com/input/?i=solve+s%3D(ry-2p-h)*(y-2p),+y
    #   y = (sqrt(4 r^2 p^2 - 4 r h p - 8 r p^2 + 4 r s + h^2 + 4 h p + 4 p^2) + 2 r p + h + 2 p)/(2 r)
    sqrt = math.sqrt(4 * r**2 * p**2 - 4 * r * h * p - 8 * r * p**2 + 4 * r * s + h**2 + 4 * h * p + 4 * p**2)
    y = (sqrt + 2 * r * p + h + 2 * p) / (2 * r)
    return int(y * r), int(y)


def spoiler_create(header, content, tmp_path):
    header = replace_chars(header)
    content = replace_chars(content)

    # determine required height and surface
    char_count = int(TEST_WIDTH / CHAR_WIDTH)
    text = split_spoiler_lines(content, char_count)
    cmd = [x.format(user_text=text, font=FONT_PATH, pad=PADDING) for x in ffmpeg_generate_height.split(" ")]
    ffmpeg_output = subprocess.run(["ffmpeg"] + cmd, universal_newlines=True, stderr=subprocess.PIPE)
    test_height = float(ffmpeg_output.stderr.split()[1])
    surface = TEST_WIDTH * test_height

    if surface > 8300000:
        return False
    elif test_height > 5000:
        return False
    elif test_height < 50:
        return False

    width, height = dimensions(surface)
    char_count = int(width / CHAR_WIDTH)

    # final render
    header = split_spoiler_lines(header, char_count)
    text = split_spoiler_lines(content, char_count)
    cmd = [x.format(user_header=header, user_text=text, width=width, height=height, font=FONT_PATH,
                    pad=PADDING, out_path=tmp_path) for x in ffmpeg_output_cmd.split(" ")]
    subprocess.run(["ffmpeg"] + cmd, universal_newlines=True)
    return True


def spoiler_image(header, image, width, height, tmp_path):
    header = replace_chars(header)

    char_count = int(width / CHAR_WIDTH)

    # final render
    header = split_spoiler_lines(header, char_count)
    cmd = [x.format(user_header=header, image=image, width=width, height=height, font=FONT_PATH,
                    pad=PADDING, out_path=tmp_path) for x in ffmpeg_image_cmd.split(" ")]
    subprocess.run(["ffmpeg"] + cmd, universal_newlines=True)
    return True


async def check_message(message):
    if not message.attachments:
        await private_msg(message, "Picture as attachment is needed.")
    elif not message.attachments[0].width:
        await private_msg(message, "Filetype is not allowed!")
    elif message.attachments[0].width * message.attachments[0].height > 8300000:
        await private_msg(message, "Picture is too big.")
    elif message.attachments[0].width < 100:
        await private_msg(message, "Picture width is too small.")
    elif message.attachments[0].height < 100:
        await private_msg(message, "Picture height is too small.")
    else:
        return True
    raise ImageFailed


@register_command('spoiler', description='Create webm with spoiler warning.')
@add_argument('title', help='Spoiler title.')
@add_group('-t', '--text', help='Spoiler text.')
@add_group('-i', '--image', action="store_true", help='Spoiler image [attachment].')
async def spoiler(_, message, args):
    try:
        image = None
        if args.image and await check_message(message):
            img_url = message.attachments[0].url
            filename = message.attachments[0].filename
            width = message.attachments[0].width
            height = message.attachments[0].height
            image = await utils.get_file(img_url, tmp_path, filename, message=message)
            if image is None:
                return await private_msg(message, "Can't load image. Pls try it again later.")

        await delete_user_message(message)
        await private_msg(message, f"```{message.content}```")
        spoiler_title = f"Spoiler: {args.title} (by {message.author.display_name})"
        content = f"**Spoiler: {args.title}** (by <@!{message.author.id}>)"

        if image is not None:
            check = spoiler_image(spoiler_title, image, width, height, tmp_path)
        else:
            check = spoiler_create(spoiler_title, args.text, tmp_path)

        if check:
            await message.channel.send(file=discord.File(f'{tmp_path}/spoiler.webm'), content=content)
        else:
            await private_msg(message, "Title/Text is too short/long.")
    except ImageFailed:
        pass
    finally:
        await delete_user_message(message)
