import random

import asyncio
from pyrogram import Client

from config import SESSIONS_FOLDER
from src.create_bot import bot


async def auth_session(session_name: str, app_id: int, api_hash: str):
    bot_username = (await bot.get_me()).username

    async with Client(session_name, app_id, api_hash, workdir=SESSIONS_FOLDER) as app:
        await app.send_message(bot_username, '/start')


_global_clients = []
_client_lock = asyncio.Lock()


async def load_clients():
    with open(f"{SESSIONS_FOLDER}/registry.txt", 'r') as registry:
        sessions_data = registry.read().split('\n')

    for data in sessions_data:
        name, app_id, api_hash = data.split('|')
        client = Client(name, app_id, api_hash, workdir='sessions/')
        await client.start()
        client.is_busy = False
        _global_clients.append(client)


def release_pyrogram_client(client):
    client.is_busy = False


async def get_pyrogram_client():
    global _global_clients

    async with _client_lock:
        if not _global_clients:
            await load_clients()

        # Выбираем случайного клиента из списка доступных
        available_clients = [client for client in _global_clients if not client.is_busy]
        if available_clients:
            chosen_client = random.choice(available_clients)
            chosen_client.is_busy = True
            return chosen_client
        else:
            # Если все клиенты заняты, возвращаем случайного клиента из общего списка
            return random.choice(_global_clients)
