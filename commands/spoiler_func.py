import re
import aiohttp
import itertools
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
import PIL.ImageSequence
from math import ceil
from images2gif import writeGif
from handle_messages import private_msg, delete_user_message
from cmd_manager.decorators import register_command, add_argument
import tempfile

path_font = "/home/infi/OpenSans-Regular.ttf"
# TODO Rewrite with Wand


def text_replace(text):
    text = text.replace("  ", " ")
    text = text.replace("„", "“")
    text = text.replace("\"", "“")
    text = text.replace("‒", "-")

    return text


def create_image(text, width, height, images, font, tmp_path, number, img=None, rgb=None):
    if not img:
        img = PIL.Image.new('RGB', (width, height), (58, 61, 66))
        d = PIL.ImageDraw.Draw(img)
        d.text((10, 10), text, fill=(200, 200, 200), font=font)
        img.save(f"{tmp_path}/{number}.png", "png")
        test = PIL.Image.open(f"{tmp_path}/{number}.png")
        background = PIL.Image.new("RGB", (width + 30, height + 30), (70, 75, 80))
        img_w, img_h = test.size
        bg_w, bg_h = background.size
        offset = (int((bg_w - img_w) / 2), int((bg_h - img_h) / 2))
        background.paste(test, offset)
        background.save(f"{tmp_path}/{number}.png")
    else:
        img = PIL.Image.new(f'{rgb}', (width, height), (58, 61, 66, 1))
        d = PIL.ImageDraw.Draw(img)
        d.text((10, 10), text, fill=(200, 200, 200), font=font)
        img.save(f"{tmp_path}/{number}.png", "png")
    images.append(PIL.Image.open(f"{tmp_path}/{number}.png"))

    return images


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


def spoiler_create(start_text, text, tmp_path):
    height = ceil(len(text) / 55) * 60
    for i in range(text.count("\n")):
        height += 60

    if height < 700:
        height += 120
        width = 1100
        font = PIL.ImageFont.truetype(path_font, 45)
        font_front = PIL.ImageFont.truetype(path_font, 45)
        start_text = split_spoiler_lines(start_text, 42)
        text = split_spoiler_lines(text, 45)
    elif height < 1400:
        height += 200
        width = 2100
        font = PIL.ImageFont.truetype(path_font, 65)
        font_front = PIL.ImageFont.truetype(path_font, 120)
        start_text = split_spoiler_lines(start_text, 41)
        text = split_spoiler_lines(text, 63)
    else:
        height += 360
        width = 3600
        font = PIL.ImageFont.truetype(path_font, 90)
        font_front = PIL.ImageFont.truetype(path_font, 180)
        start_text = split_spoiler_lines(start_text, 47)
        text = split_spoiler_lines(text, 80)

    images = []
    text = text_replace(text)
    start_text = text_replace(start_text)
    images = create_image(start_text, width, height, images, font_front, tmp_path, number=1)
    images = create_image(text, width, height, images, font, tmp_path, number=2)

    writeGif(f"{tmp_path}/animation.gif", images, repeat=False, duration=1)


async def spoiler_create_image(message, attachments, tmp_path, error_message):
    img_url = attachments[0]["url"]
    height = attachments[0]["height"]
    width = attachments[0]["width"]
    name = attachments[0]["filename"]
    if height < 400:
        font_front = PIL.ImageFont.truetype(path_font, 25)
        message = split_spoiler_lines(message, 25)
    elif height < 700:
        font_front = PIL.ImageFont.truetype(path_font, 45)
        message = split_spoiler_lines(message, 45)
    elif height < 1400:
        font_front = PIL.ImageFont.truetype(path_font, 120)
        message = split_spoiler_lines(message, 63)
    else:
        font_front = PIL.ImageFont.truetype(path_font, 180)
        message = split_spoiler_lines(message, 80)

    start_text = text_replace(message)
    images = []
    if ".png" in name:
        images = create_image(start_text, width, height, images, font_front, tmp_path, number=1, img=True, rgb="RGBA")
    else:
        images = create_image(start_text, width, height, images, font_front, tmp_path, number=1, img=True, rgb="RGB")

    with aiohttp.ClientSession() as sess:
        async with sess.get(img_url) as resp:
            if resp.status == 200:
                with open(f"{tmp_path}/{name}", 'wb') as f:
                    f.write(await resp.read())
                images.append(PIL.Image.open(f"{tmp_path}/{name}"))
                writeGif(f"{tmp_path}/animation.gif", images, repeat=False, duration=1)
            else:
                await private_msg(error_message, "Error cant load the picture. Pls wait and try it again.")
                return True


@register_command('spoiler', description='Convert your message content to GIF with spoiler warning.')
@add_argument('title', help='Spoiler title.')
async def spoiler(client, message, args):
    forbidden_error = False
    tmp_path_dir = tempfile.TemporaryDirectory()
    tmp_path = tmp_path_dir.name
    await delete_user_message(message)
    await private_msg(message, f"```{message.content}```")
    segments = message.content.split("\n", 1)
    author = str(message.author).split("#")[0]
    wspoiler = args.title
    spoiler_title = f"Spoiler: {args.title} (by {author})"
    if len(segments) < 2:
        forbidden_error = await spoiler_create_image(spoiler_title, message.attachments, tmp_path, message)
        content = f"**Spoiler: {wspoiler}** (by <@!{message.author.id}>)\nOriginal Link: <{message.attachments[0]['url']}>"
    else:
        spoiler_content = segments[1]
        spoiler_create(spoiler_title, spoiler_content, tmp_path)
        content = f"**Spoiler: {wspoiler}** (by <@!{message.author.id}>)"

    if not forbidden_error:
        await client.send_file(message.channel, f"{tmp_path}/animation.gif", content=content)
