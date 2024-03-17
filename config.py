import os
from typing import Final
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

BOT_TOKEN: Final[str] = os.getenv('BOT_TOKEN', 'define me')
OWNER_IDS: Final[tuple] = tuple(int(i) for i in str(os.getenv('BOT_OWNER_IDS')).split(','))

cwd = os.getcwd()
VIDEOS_FOLDER: Final[str] = os.path.join(cwd, 'videos')
SESSIONS_FOLDER: Final[str] = os.path.join(cwd, 'sessions')

MAX_VIDEO_FILE_SIZE_MB = 200
