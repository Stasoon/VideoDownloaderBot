import re
import os.path
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import aiofiles

import aiohttp
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InputFile, BufferedInputFile

from config import VIDEOS_FOLDER
from src.database import advertisements
from src.utils import logger
from src.utils.pyrogram_clients import get_pyrogram_client, release_pyrogram_client
from src.utils.video_data import VideoData


async def __load_thumb(url: str) -> BytesIO | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = BytesIO(await response.content.read())
                data.seek(0)
    except Exception as e:
        return None

    return data


def get_safe_filename(filename) -> str:
    safe_name = re.sub(r"[^A-zА-я0-9+\s]", "", filename)
    return safe_name


async def send_advertisement(bot: Bot, user_id: int):
    """ Отправляет рекламу """
    count = advertisements.increase_counter_and_get_value(user_id=user_id)
    show_ad_every = 4
    if count < show_ad_every:
        return

    ad = advertisements.get_random_ad()
    if not ad:
        return

    advertisements.reset_counter(user_id=user_id)
    text = ad.text
    markup = ad.markup_json

    await bot.send_message(
        chat_id=user_id, text=text, reply_markup=markup,
        disable_web_page_preview=not ad.show_preview, parse_mode='HTML'
    )


async def get_media_file_url(bot: Bot, message: Message) -> str | None:
    """ Возвращает ссылку из бота на файл, прикреплённый к сообщению """
    bot_token = bot.token
    media = None

    if message.voice:
        media = message.voice
    elif message.audio:
        media = message.audio
    elif message.video_note:
        media = message.video_note
    elif message.video:
        media = message.video

    if media:
        file = await bot.get_file(media.file_id)
        return f'https://api.telegram.org/file/bot{bot_token}/{file.file_path}'
    return None


async def send_video(
        bot: Bot, chat_id: int, file: str | InputFile, video_data: VideoData = None
) -> str:

    if video_data:
        w, h = video_data.resolution
        duration = video_data.duration

        thumb = None
        if video_data.thumbnail_url:
            thumb_data = await __load_thumb(url=video_data.thumbnail_url)
            if thumb_data:
                thumb = BufferedInputFile(thumb_data.read(), filename='thumb.jpg')
    else:
        w, h, duration, thumb = [None] * 4

    video_msg = await bot.send_video(
        chat_id=chat_id, video=file,
        protect_content=False, supports_streaming=True,
        duration=duration, width=w, height=h, thumbnail=thumb
    )

    await send_advertisement(bot=bot, user_id=chat_id)

    if video_msg.video:
        return video_msg.video.file_id
    elif video_msg.animation.file_id:
        return video_msg.animation.file_id


async def __send_big_video(bot_username: str, video_data: VideoData):
    app = await get_pyrogram_client()

    thumb = None
    if video_data.thumbnail_url:
        thumb = await __load_thumb(video_data.thumbnail_url)

    try:
        video_msg = await app.send_video(
            chat_id=bot_username, video=video_data.file_path,
            supports_streaming=True, file_name=video_data.title,
            duration=video_data.duration, protect_content=False,
            width=video_data.resolution[0], height=video_data.resolution[1],
            thumb=thumb
        )
        video_file_id = video_msg.video.file_id
    except Exception as e:
        logger.error(e)
        video_file_id = None

    release_pyrogram_client(app)
    yield video_file_id, video_data.file_path


async def __load_video_and_get_file_id(bot_username: str, video_data: VideoData):
    """Скачивает видео, а затем отправляет в чат с ботом. Возвращает file_id видео."""
    if video_data.title:
        filename = video_data.title if video_data.title.endswith('.mp4') else f"{video_data.title}.mp4"
    else:
        filename = f"{bot_username}_{str(datetime.today())}.mp4"

    file = f"{str(uuid4())[:10]}_{filename}"
    file_path = os.path.join(VIDEOS_FOLDER, get_safe_filename(file))

    async with aiohttp.ClientSession() as session:
        async with session.get(video_data.file_url) as response:
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in response.content.iter_any():
                    await f.write(chunk)

    app = await get_pyrogram_client()
    video_file_id = None

    thumb = None
    if video_data.thumbnail_url:
        thumb = await __load_thumb(video_data.thumbnail_url)

    try:
        video_msg = await app.send_video(
            chat_id=bot_username, video=file_path,
            supports_streaming=True, file_name=filename,
            protect_content=False, duration=video_data.duration,
            width=video_data.resolution[0], height=video_data.resolution[1],
            thumb=thumb
        )
        video_file_id = video_msg.video.file_id
    except Exception as e:
        logger.error(e)

    release_pyrogram_client(app)
    yield video_file_id, file_path


async def process_video(bot_username: str, video_data: VideoData):
    if video_data.file_url is None and video_data.file_path is None:
        return

    if video_data.file_url:
        meth = __load_video_and_get_file_id
        params = {'bot_username': bot_username, 'video_data': video_data}
    elif video_data.file_path:
        meth = __send_big_video
        params = {'bot_username': bot_username, 'video_data': video_data}

    async for file_id, file_path in meth(**params):
        # Удаляем файл после использования
        if os.path.exists(file_path):
            os.remove(file_path)

        return file_id


def send_and_delete_timer():
    """ Перед отработкой хэндлера отправляет песочные часы, и удаляет их после отработки хэндлера """
    def decorator(func):
        async def wrapper(update: Message | CallbackQuery, *args, **kwargs):
            if isinstance(update, CallbackQuery):
                message = update.message
            else:
                message = update

            timer_msg = await message.answer('⏳')
            await func(update, *args, **kwargs)

            await timer_msg.delete()
        return wrapper
    return decorator

