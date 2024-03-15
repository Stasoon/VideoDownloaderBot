from typing import Any, Union, Dict

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import AiogramError
from aiogram.types import CallbackQuery, Message
from aiogram.filters import BaseFilter
from aiogram import Bot

from src.database.subscription_channels import get_channels, get_channel_ids
from src.utils import logger


async def get_not_subscribed_channels(bot, user_id):
    not_subbed_channels = [
        channel for channel in get_channels()
        if not await check_status_in_channel_is_member(bot, channel.channel_id, user_id)
    ]
    return not_subbed_channels


async def check_status_in_channel_is_member(bot: Bot, channel_id: int, user_id: int) -> bool:
    try:
        user = await bot.get_chat_member(channel_id, user_id)
    except AiogramError as e:
        logger.exception(e)
        return True

    if user.status != ChatMemberStatus.LEFT:
        return True
    return False


class IsSubscriberFilter(BaseFilter):
    """ Фильтр проверки подписки """

    def __init__(self, should_be_subscriber: bool = True):
        self.is_sub = should_be_subscriber

    async def __call__(self, event: Union[Message, CallbackQuery], *args, **kwargs) -> Union[bool, Dict[str, Any]]:
        # if has_subscription(user_id=event.from_user.id):
        #     return self.is_sub is True
        for channel_id in get_channel_ids():
            if not await check_status_in_channel_is_member(event.bot, channel_id, event.from_user.id):
                return self.is_sub is False

        return self.is_sub is True
