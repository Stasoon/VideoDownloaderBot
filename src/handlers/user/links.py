import os.path
from urllib.parse import urlparse

import aiohttp
from aiogram import Router, F
from aiogram.types import Message, URLInputFile, FSInputFile

from config import MAX_VIDEO_FILE_SIZE_MB
from src.database.cached_videos import get_cached_video, save_video_to_cache, VideoSource
from src.filters.is_subscriber import IsSubscriberFilter
from src.filters.video_source import VideoSourceFilter
from src.messages.user import UserMessages
from src.utils.downloaders import YoutubeDownloader, PinterestDownloader, InstagramDownloader, TikTokDownloader
from src.utils.message_utils import send_and_delete_timer, send_video, process_video
from src.utils.downloader import Downloader
from src.utils import logger


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
            return Downloader
        case _:
            return Downloader


@send_and_delete_timer()
async def _handle_link_message(message: Message, source: VideoSource, **kwargs):
    video_key, filename = await Downloader(message.text).get_video_info()
    # Если нет информации о видео
    if not video_key and not filename:
        await message.reply(text=UserMessages.get_video_not_found())
        return

    # Если видео уже скачивалось
    video_from_cache = get_cached_video(key=video_key, source=source)
    if video_from_cache:
        await send_video(bot=message.bot, chat_id=message.from_user.id, file=video_from_cache.telegram_file_id)
        return

    # Получаем ссылку на скачивание видео
    downloader = get_downloader(source)(message.text)

    try:
        filename, video_url = await downloader.get_video_file_url()
    except Exception as e:
        await message.reply(text=UserMessages.get_download_error())
        logger.error(e)
        return

    if not video_url:
        await message.reply(text=UserMessages.get_download_error())
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as response:
            content_size_bit = response.content_length

    max_input_file_size_mb = 48
    content_size_mb = content_size_bit // 1024**2
    try:
        if content_size_mb > MAX_VIDEO_FILE_SIZE_MB:
            raise Exception(f'file size > {MAX_VIDEO_FILE_SIZE_MB}')
        elif content_size_mb > max_input_file_size_mb:
            bot_username = (await message.bot.get_me()).username
            file = await process_video(bot_username=bot_username, video_url=video_url, filename=filename)
        else:
            file = URLInputFile(video_url, filename=filename)

        file_id = await send_video(bot=message.bot, chat_id=message.from_user.id, file=file)
    except Exception as e:
        logger.error(e)
        await message.reply(text=UserMessages.get_download_error())
        return

    save_video_to_cache(file_id=file_id, key=video_key, source=source)


@send_and_delete_timer()
async def handle_vk_link_message(message: Message, source: VideoSource, **kwargs):
    downloader = Downloader(video_url=message.text)
    key, title, file_path = await downloader.get_video_file_url()

    video_from_cache = get_cached_video(key=key, source=source)

    if video_from_cache:
        await send_video(bot=message.bot, chat_id=message.from_user.id, file=video_from_cache.telegram_file_id)
        return

    if os.path.exists(file_path):
        size = os.path.getsize(file_path) // 1024**2
    else:
        await message.answer(UserMessages.get_download_error())
        return

    if size > 48:
        bot_username = (await message.bot.get_me()).username
        file_id = await process_video(bot_username=bot_username, video_fs_path=file_path, filename=title)
        await send_video(bot=message.bot, chat_id=message.from_user.id, file=file_id)
    else:
        file = FSInputFile(file_path)
        file_id = await send_video(bot=message.bot, chat_id=message.from_user.id, file=file)

    save_video_to_cache(file_id=file_id, key=key, source=source)


def register_links_handlers(router: Router):
    router.message.filter(IsSubscriberFilter(should_be_subscriber=True))

    # Тик-ток
    router.message.register(
        _handle_link_message, F.text.startswith('https://'), F.text.contains('tiktok'),
        VideoSourceFilter(VideoSource.TIKTOK)
    )

    # Инстаграм
    router.message.register(
        _handle_link_message, F.text.startswith('https://'), F.text.contains('instagram'),
        VideoSourceFilter(VideoSource.INSTAGRAM)
    )

    # Ютуб
    router.message.register(
        _handle_link_message,
        F.text.startswith('https://'),
        F.text.contains('youtu.be') | F.text.contains('youtube'),
        VideoSourceFilter(VideoSource.YOUTUBE)
    )

    # Пинтерест
    router.message.register(
        _handle_link_message,
        F.text.startswith('https://'),
        F.text.contains('pinterest') | F.text.contains('pin.it'),
        VideoSourceFilter(VideoSource.PINTEREST)
    )

    # VK
    router.message.register(
        handle_vk_link_message,
        F.text.startswith('https://'), F.text.contains('vk.com'),
        VideoSourceFilter(VideoSource.VK)
    )
