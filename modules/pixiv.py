import datetime
import io
import logging
import re

import discord
import pixivpy_async as pixiv

from config import config

__all__ = [
    'handle_pixiv',
]

# https://www.pixiv.net/en/artworks/67500589
pixiv_pattern = re.compile(r'(https://www\.pixiv\.net/\S*artworks/(\d*))')
# https://i.pximg.net/img-original/img/2018/02/28/09/04/31/67500589_p0.jpg
pixiv_direct_img_pattern = re.compile(r'https://i\.pximg\.net/\S+\.\w+\b')

# global pixiv app-api instance
_aapi = None


async def _assert_pixiv_aapi():
    global _aapi
    if not _aapi:
        aapi = pixiv.AppPixivAPI()
        try:
            await aapi.login(config.MAIN.pixiv_username, config.MAIN.pixiv_password)
        except pixiv.error.AuthCredentialsError:
            logging.error("bad pixiv credentials")
            return False
        except Exception:
            logging.exception("error during pixiv auth")
            return False
        else:
            _aapi = aapi

    return _aapi


async def handle_pixiv(message: discord.Message) -> None:
    ids = pixiv_pattern.findall(message.content)
    imgs = pixiv_direct_img_pattern.findall(message.content)
    if not (ids or imgs) or not (aapi := await _assert_pixiv_aapi()):
        return

    is_guild = isinstance(message.channel, discord.abc.GuildChannel)
    now = datetime.datetime.today().strftime("%a %d %b %H:%M:%S")

    async with message.channel.typing():
        for url, illust_id in ids[:5]:  # limit to 5, like discord does
            if is_guild:
                logging.info(f"Date: {now} User: {message.author} Server: {message.guild.name} "
                             f"Channel: {message.channel.name} Pixiv Url: {url}")

            response = await aapi.illust_detail(illust_id)
            if response.get('has_error'):
                logging.error(f"Error fetching illustration {illust_id}: {response.errors}")
                return

            ill = response.illust
            text = f"{ill.title} by {ill.user.name}"
            if ill.page_count > 1:
                text += f" [{ill.page_count} pages]"
            else:
                text += f" ({ill.width}x{ill.height})"
            text += f"\n<{url}>"

            await post_image(message, text, ill.image_urls.large)

        for image_url in imgs[:5]:
            if is_guild:
                logging.info(f"Date: {now} User: {message.author} Server: {message.guild.name} "
                             f"Channel: {message.channel.name} Pixiv Url: {image_url}")

            await post_image(message, "", image_url)


async def post_image(message: discord.Message, text: str, image_url: str) -> None:
    aapi = await _assert_pixiv_aapi()
    with io.BytesIO() as bio:
        bio.name = image_url.rsplit('/', 1)[-1]
        await aapi.download(image_url, fname=bio)
        bio.seek(0)
        await message.channel.send(text, file=discord.File(bio),
                                   reference=message, mention_author=False)
