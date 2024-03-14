from urllib.parse import urlparse

import aiohttp
from aiogram import Router, F
from aiogram.types import Message, URLInputFile

from src.database.cached_videos import get_cached_video, save_video_to_cache, VideoSource
from src.filters.video_source import VideoSourceFilter
from src.utils.message_utils import send_and_delete_timer, send_video, load_video_and_get_file_id
from src.utils.downloaders import YoutubeDownloader, InstagramDownloader, PinterestDownloader, TikTokDownloader, VkDownloader


def get_video_path(url):
    return urlparse(url).path


def get_downloader(link_source: VideoSource):
    match link_source:
        case VideoSource.TIKTOK:
            return TikTokDownloader
        case VideoSource.INSTAGRAM:
            return InstagramDownloader
        case VideoSource.YOUTUBE:
            return YoutubeDownloader
        case VideoSource.PINTEREST:
            return PinterestDownloader
        case VideoSource.VK:
            return VkDownloader


@send_and_delete_timer()
async def handle_link_message(message: Message, source: VideoSource, **kwargs):
    video_key = get_video_path(message.text)
    video_from_cache = get_cached_video(key=video_key, source=source)

    if video_from_cache:
        await send_video(bot=message.bot, chat_id=message.from_user.id, file=video_from_cache.telegram_file_id)
        return

    downloader = get_downloader(source)(message.text)
    filename, video_url = await downloader.get_video_file_url()

    if not video_url:
        await message.answer('Не удалось скачать видео')
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as response:
            content_size = response.content_length

    if content_size // 1024**2 > 10:
        file_id = await load_video_and_get_file_id(bot_id=message.bot.id, video_url=video_url, filename=filename)
        await send_video(bot=message.bot, chat_id=message.from_user.id, file=file_id)
    else:
        file = URLInputFile(url=video_url)
        file_id = await send_video(bot=message.bot, chat_id=message.from_user.id, file=file)

    save_video_to_cache(file_id=file_id, key=video_key, source=source)


def register_links_handlers(router: Router):
    # Тик-ток
    router.message.register(
        handle_link_message, F.text.startswith('https://'), F.text.contains('tiktok'),
        VideoSourceFilter(VideoSource.TIKTOK)
    )

    # Инстаграм
    router.message.register(
        handle_link_message, F.text.startswith('https://'), F.text.contains('instagram'),
        VideoSourceFilter(VideoSource.INSTAGRAM)
    )

    # Ютуб
    router.message.register(
        handle_link_message,
        F.text.startswith('https://'),
        F.text.contains('youtu.be') | F.text.contains('youtube'),
        VideoSourceFilter(VideoSource.YOUTUBE)
    )

    # Пинтерест
    router.message.register(
        handle_link_message,
        F.text.startswith('https://'),
        F.text.contains('pinterest') | F.text.contains('pin.it'),
        VideoSourceFilter(VideoSource.PINTEREST)
    )

    # VK
    router.message.register(
        handle_link_message,
        F.text.startswith('https://'), F.text.contains('vk.com'),
        VideoSourceFilter(VideoSource.VK)
    )
