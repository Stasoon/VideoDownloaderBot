import asyncio

from src.start_bot import start_bot
from src.utils import setup_logger


async def main():
    # from config import CLIENT_SESSION_NAME
    # from src.utils.authorize_pyrogram import auth_session
    # await auth_session(CLIENT_SESSION_NAME, 27390183, '335ab280de4415bdba413bef3095dd74')

    setup_logger()
    await start_bot()


if __name__ == '__main__':
    asyncio.run(main=main())
