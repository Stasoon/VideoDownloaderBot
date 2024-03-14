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

