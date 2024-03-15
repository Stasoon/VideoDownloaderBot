from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.database.reflinks import increase_op_count
from src.filters.is_subscriber import IsSubscriberFilter, get_not_subscribed_channels
from src.messages.user import UserMessages
from src.keyboards.user import UserKeyboards


async def handle_not_subscriber_message(message: Message):
    user_id = message.from_user.id
    channels = await get_not_subscribed_channels(message.bot, user_id)

    text = UserMessages.get_user_must_subscribe()
    markup = UserKeyboards.get_not_subbed_markup(channels)

    await message.delete()
    await message.answer(text=text, reply_markup=markup)


async def handle_user_subscribed_callback(callback: CallbackQuery):
    message = callback.message
    unsubbed_channels = await get_not_subscribed_channels(message.bot, callback.from_user.id)

    if not unsubbed_channels:
        await callback.answer(text=UserMessages.get_user_subscribed(), show_alert=True)
        increase_op_count(callback.from_user.id)
        await message.delete()
    else:
        await callback.answer(text=UserMessages.get_not_all_channels_subscribed(), show_alert=True)


def register_not_subs_handlers(router: Router):
    # Нажатие на кнопку "Я подписался"
    router.callback_query.register(
        handle_user_subscribed_callback,
        F.data == 'check_subscription'
    )

    # Действия при отсутствии подписки
    router.message.register(handle_not_subscriber_message, IsSubscriberFilter(False))
