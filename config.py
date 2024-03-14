import os
from typing import Final
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

BOT_TOKEN: Final[str] = os.getenv('BOT_TOKEN', 'define me')
OWNER_IDS: Final[tuple] = tuple(int(i) for i in str(os.getenv('BOT_OWNER_IDS')).split(','))

VIDEOS_FOLDER: Final[str] = 'videos/'

CLIENT_NAME: Final[str] = os.getenv('CLIENT_NAME')
CLIENT_API_ID: Final[int] = int(os.getenv('CLIENT_API_ID'))
CLIENT_API_HASH: Final[str] = os.getenv('CLIENT_API_HASH')
