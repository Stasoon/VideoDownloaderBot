import hashlib
import os.path
from datetime import datetime
import aiofiles

import aiohttp
from aiogram import Bot
from aiogram.exceptions import AiogramError
from aiogram.types import Message, CallbackQuery, InputFile
from pyrogram import Client

from config import CLIENT_NAME, CLIENT_API_ID, CLIENT_API_HASH, VIDEOS_FOLDER
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


async def load_video_and_get_file_id(bot_id: int, video_url: str, filename: str = None):
    """ Отправляет видео в нужный чат. Возвращает file_id видео """

    if filename:
        filename = filename if filename.endswith('.mp4') else f"{filename}.mp4"
    else:
        timestamp = str(datetime.now())
        filename = f"{hashlib.md5(timestamp.encode()).hexdigest()}.mp4"

    file_path = os.path.join(VIDEOS_FOLDER, filename)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=10)) as session:
        async with session.get(video_url) as response:
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in response.content.iter_any():
                    await f.write(chunk)

    async with Client(CLIENT_NAME, CLIENT_API_ID, CLIENT_API_HASH) as app:
        video_msg = await app.send_video(
            chat_id=bot_id, video=file_path,
            supports_streaming=True, file_name=filename
        )
        video_file_id = video_msg.video.file_id

    if os.path.exists(file_path):
        os.remove(path=file_path)

    return video_file_id


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


# async def send_audio_message(bot: Bot, chat_id: int, file, song_title=None, artist_name=None, cover=None) -> Message:
#     """ Отправляет песню с подписью """
#     bot_username = (await bot.get_me()).username
#
#     default_cover = await Config.get_default_cover()
#     if default_cover or (default_cover and not cover):
#         cover = default_cover
#
#     audio_message = await bot.send_audio(
#         chat_id=chat_id, audio=file, title=song_title,
#         performer=artist_name, thumb=cover,
#         caption=UserMessages.get_audio_file_caption(bot_username=bot_username),
#     )
#     return audio_message
#
#
# async def send_channels_to_subscribe(bot, user_id):
#     """ Показывает сообщение с просьбой подписаться, нужные каналы и кнопку проверки"""
#     channels_to_subscribe = await get_not_subscribed_channels(bot=bot, user_id=user_id)
#     markup = UserKeyboards.get_not_subbed_markup(channels_to_subscribe)
#     text = UserMessages.get_user_must_subscribe()
#     await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
