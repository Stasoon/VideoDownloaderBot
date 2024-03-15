import hashlib
import os.path
from datetime import datetime
from uuid import uuid4

import aiofiles

import aiohttp
from aiogram import Bot
from aiogram.exceptions import AiogramError
from aiogram.types import Message, CallbackQuery, InputFile
from pyrogram import Client

from config import VIDEOS_FOLDER
from src.utils import logger


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


async def send_video(bot: Bot, chat_id: int, file: str | InputFile) -> str:
    video_msg = await bot.send_video(
        chat_id=chat_id, video=file,
        protect_content=False, supports_streaming=True
    )

    if video_msg.video:
        return video_msg.video.file_id
    elif video_msg.animation.file_id:
        return video_msg.animation.file_id


global_client = None


async def get_pyrogram_client(session_name):
    global global_client
    if global_client is None:
        global_client = Client(session_name, workdir='sessions/')
        await global_client.start()
    return global_client


async def __send_and_delete_big_video(bot_username: str, video_path: str, filename: str = None):
    app = await get_pyrogram_client('stas')

    try:
        video_msg = await app.send_video(
            chat_id=bot_username, video=video_path,
            supports_streaming=True, file_name=filename,
            protect_content=False, width=1920, height=1080
        )
        video_file_id = video_msg.video.file_id
    except Exception as e:
        logger.error(e)
        video_file_id = None

    yield video_file_id, video_path


async def __load_video_and_get_file_id(bot_username: str, video_url: str, filename: str = None):
    """Скачивает видео, а затем отправляет в чат с ботом. Возвращает file_id видео."""
    if filename:
        filename = filename if filename.endswith('.mp4') else f"{filename}.mp4"
    else:
        filename = f"{bot_username}_{str(datetime.today())}.mp4"

    file_path = os.path.join(VIDEOS_FOLDER, f"{str(uuid4())[:10]}_{filename}")

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=10)) as session:
        async with session.get(video_url) as response:
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in response.content.iter_any():
                    await f.write(chunk)

    app = await get_pyrogram_client('stas')
    video_file_id = None

    try:
        video_msg = await app.send_video(
            chat_id=bot_username, video=file_path,
            supports_streaming=True, file_name=filename,
            protect_content=False, width=1920, height=1080
        )
        video_file_id = video_msg.video.file_id
    except Exception as e:
        logger.error(e)

    yield video_file_id, file_path


async def process_video(
        bot_username: str, video_url: str = None, video_fs_path: str = None, filename: str = None
):
    if video_url is None and video_fs_path is None:
        return

    if video_url:
        meth = __load_video_and_get_file_id
        params = {'bot_username': bot_username, 'video_url': video_url, 'filename': filename}
    elif video_fs_path:
        meth = __send_and_delete_big_video
        params = {'bot_username': bot_username, 'video_path': video_fs_path, 'filename': filename}

    async for file_id, file_path in meth(**params): #__load_video_and_get_file_id(bot_username, video_url, filename):
        # Используем video_id
        print("Video File ID:", file_id, file_path)

        # Удаляем файл после использования
        if os.path.exists(file_path):
            print(f'удаляю {file_path}')
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

            try:
                await timer_msg.delete()
            except AiogramError:
                pass
        return wrapper
    return decorator

