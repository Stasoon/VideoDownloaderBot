import calendar
from datetime import date

from aiogram.types import KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardBuilder


class UserKeyboards:

    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='')
        return None

    @classmethod
    def get_not_subbed_markup(cls, channels_to_sub) -> InlineKeyboardMarkup | None:
        """
        Возвращает клавиатуру с каналами, на которые должен подписаться пользователь,
        и кнопкой 'Проверить подписку'
        """
        if len(channels_to_sub) == 0:
            return None

        builder = InlineKeyboardBuilder()
        for channel in channels_to_sub:
            builder.button(text=channel.title, url=channel.url)
        builder.button(text='✅ Проверить ✅', callback_data='check_subscription')

        builder.adjust(1)
        return builder.as_markup()

