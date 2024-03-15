from pyrogram import Client

from config import SESSIONS_FOLDER
from src.create_bot import bot


async def auth_session(session_name: str, app_id: int, api_hash: str):
    bot_username = (await bot.get_me()).username

    async with Client(session_name, app_id, api_hash, workdir=SESSIONS_FOLDER) as app:
        await app.send_message(bot_username, '/start')

