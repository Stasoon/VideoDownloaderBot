from urllib.parse import urlparse

from aiogram import Router, F
from aiogram.exceptions import AiogramError
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatMemberStatus

from src.database.subscription_channels import get_channels, save_channel, delete_channel


# region AddChannels

class ChannelCallback(CallbackData, prefix='op_channel'):
    channel_id: int
    action: str


class SubscriptionChannelAdding(StatesGroup):
    wait_for_post = State()
    wait_for_url = State()


class Keyboards:

    @staticmethod
    def get_subchecking_menu():
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Добавить канал', callback_data='addchannel')
        builder.button(text='➖ Удалить канал', callback_data='delchannel')

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_cancel():
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Отменить', callback_data='cancel')
        return builder.as_markup()

    @staticmethod
    def get_channels_markup(channels_to_delete: list = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        if channels_to_delete:
            for channel in get_channels():
                builder.button(
                    text=channel.title,
                    callback_data=ChannelCallback(channel_id=channel.channel_id, action='delete')
                )

        builder.button(text='🔙 Отменить', callback_data='cancel')
        builder.adjust(1)
        return builder.as_markup()


async def send_subchecking_menu(message: Message):
    text = '📲 Каналы на ОП: \n\n'
    text += " \n".join(
        f"{n}) <a href='{channel.url}'>{channel.title}</a>" for n, channel in enumerate(get_channels(), start=1)
    ) + ' \n\nЧто вы хотите сделать?'
    await message.answer(text=text, reply_markup=Keyboards.get_subchecking_menu())


async def __handle_subchecking_message(message: Message) -> None:
    await send_subchecking_menu(message)


async def __handle_addchannel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer(
        '1) Пригласите бота в нужный канал \n'
        '2) Назначьте его администратором, чтобы он мог видеть участников \n'
        '3) Перешлите сюда любой пост из канала',
        reply_markup=Keyboards.get_channels_markup(channels_to_delete=None)
    )
    await state.set_state(SubscriptionChannelAdding.wait_for_post)


async def __handle_channel_post_message(message: Message, state: FSMContext):
    if not message.forward_from_chat:
        await message.answer('Это не пост из канала! Отправьте боту пост из канала, который хотите добавить')
        return

    try:
        channel = message.forward_from_chat
        bot_as_member = await channel.get_member(message.bot.id)
        if bot_as_member.status != ChatMemberStatus.ADMINISTRATOR:
            raise AiogramError
    except AiogramError:
        await message.answer(
            'Бот не является админом в чате! Сделайте бота админом в канале, чтобы он мог видеть участников, '
            'и повторите попытку. '
        )
    except AttributeError:
        await message.answer('Это не сообщение из канала, либо бот не добавлен в канал! Повторите попытку')
    else:
        await state.update_data(channel_id=channel.id, title=channel.title)
        await message.answer(
            'Теперь пришлите ссылку, по которой будут вступать пользователи:',
            reply_markup=Keyboards.get_cancel()
        )
        await state.set_state(SubscriptionChannelAdding.wait_for_url)


async def __handle_message_with_url(message: Message, state: FSMContext):
    channel_data = await state.get_data()
    parsed_url = urlparse(message.text)
    if bool(parsed_url.scheme and parsed_url.netloc):
        save_channel(channel_data.get('channel_id'), channel_data.get('title'), message.text)
        await message.answer('✅ Канал добавлен на ОП!')
        await state.clear()
    else:
        await message.answer('Это не ссылка. Отправьте ссылку, по которой будут вступать пользователи:')


async def __handle_delchannel_callback(callback: CallbackQuery) -> None:
    await callback.message.delete()
    channels = [i for i in get_channels()]
    await callback.message.answer(
        'Нажмите на канал, который хотите исключить: ',
        reply_markup=Keyboards.get_channels_markup(channels_to_delete=channels)
    )


async def __handle_delete_channel_action_callback(callback: CallbackQuery, callback_data: ChannelCallback):
    delete_channel(channel_id=callback_data.channel_id)
    await callback.message.delete()
    await callback.message.answer('✅ Канал исключён из ОП')
    await send_subchecking_menu(callback.message)


async def __handle_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await send_subchecking_menu(callback.message)


def register_necessary_subscriptions_handlers(router: Router):
    # обработка кнопки из меню админа
    router.message.register(__handle_subchecking_message, F.text == '📲 Обязательные подписки 📲')

    # обработка калбэка отмены добавления канала
    router.callback_query.register(__handle_cancel_callback, F.data == 'cancel')

    # обработка калбэка добавить канал
    router.callback_query.register(__handle_addchannel_callback, F.data == 'addchannel')

    # обработка пересланного поста для добавления канала
    router.message.register(
        __handle_channel_post_message,
        SubscriptionChannelAdding.wait_for_post
    )

    # обработка сообщения со ссылкой
    router.message.register(
        __handle_message_with_url,
        SubscriptionChannelAdding.wait_for_url
    )

    # обработка удаления канала из ОП
    router.callback_query.register(__handle_delchannel_callback, F.data == 'delchannel')
    router.callback_query.register(
        __handle_delete_channel_action_callback, ChannelCallback.filter(F.action == 'delete')
    )

# endregion
