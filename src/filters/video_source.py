from typing import Union

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import AiogramError
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from src.database.cached_videos import VideoSource


class VideoSourceFilter(BaseFilter):

    def __init__(self, source: VideoSource):
        self.source = source

    async def __call__(self, event: Union[Message, CallbackQuery], *args, **kwargs) -> dict[str, VideoSource]:
        return {'source': self.source}
