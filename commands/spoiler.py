import math
import re
import discord
import tempfile
import itertools
import subprocess
from handle_messages import private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument


FONT_PATH = "/home/encode/OpenSans-Regular.ttf"  # Path to OpenSans-Regular.ttf
# FONT_PATH = "/usr/share/fonts/TTF/DejaVuSans.ttf"
CHAR_WIDTH = 28.24  # for OpenSans 55
CHAR_HEIGHT = 62  # for OpenSans 55
TEST_WIDTH = 1920
RATIO = 1.35  # 1920x1420
PADDING = 50

ffmpeg_generate_height = """ffmpeg
-loglevel error
-f lavfi
-i color=c=black:s=2x2:d=0.06
-vf "drawtext=\
fontsize=55\
:fontfile={font}\
:text='%{{eif\\:print(th,16)\\:}}{user_text}'"
-f null
-""".replace("\n", " ")

ffmpeg_output_cmd = """ffmpeg
-loglevel error
-y
-f lavfi
-i color=c=black:s={width}x{height}:d=3
-vf "drawtext=\
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
:x={pad}:y={pad}"
-r 2
{out_path}/spoiler.webm""".replace("\n", " ")


def replace_chars(text):
    text = text.replace("  ", " ")
    text = text.replace("„", "“")
    text = text.replace("‒", "-")
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("=", "\\=")
    text = text.replace("$", "\\$")
    text = text.replace("\"", "“")
    text = text.replace("'", "\\'")
    text = text.replace("`", "\\`")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    text = text.replace("%", "\\%")

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
    cmd = ffmpeg_generate_height.format(user_text=text, font=FONT_PATH)
    ffmpeg_output = subprocess.check_output(cmd, shell=True, universal_newlines=True, stderr=subprocess.STDOUT)
    test_height = float(ffmpeg_output.split()[1])
    surface = TEST_WIDTH * test_height

    width, height = dimensions(surface)
    char_count = int(width / CHAR_WIDTH)

    # final render
    header = split_spoiler_lines(header, char_count)
    text = split_spoiler_lines(content, char_count)
    cmd = ffmpeg_output_cmd.format(user_header=header, user_text=text, width=width, height=height, font=FONT_PATH,
                                   pad=PADDING, out_path=tmp_path)
    subprocess.call(cmd, universal_newlines=True, shell=True)

    """
    s=(x+2p+h)*(x/r+2p)
    s=(ry+2p+h)*(y+2p)
    s=ry²+ry2p+2py+4p²+hy+2ph
    s=ry²+ry2p+2py+4p²+hy+2ph
    """


@register_command('spoiler', description='Create webm with spoiler warning.')
@add_argument('title', help='Spoiler title.')
@add_argument('content', help='Spoiler content.')
async def spoiler(_, message, args):
    tmp_path_dir = tempfile.TemporaryDirectory()
    tmp_path = tmp_path_dir.name
    await delete_user_message(message)
    await private_msg(message, f"```{message.content}```")

    spoiler_title = f"Spoiler: {args.title} (by {message.author.display_name})"
    spoiler_create(spoiler_title, args.content, tmp_path)
    content = f"**Spoiler: {args.title}** (by <@!{message.author.id}>)"

    await message.channel.send(file=discord.File(f'{tmp_path}/spoiler.webm'), content=content)
