from typing import Optional

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.reflinks import create_reflink, is_reflink_exists, get_all_links, delete_reflink


class ReferralLinksCallback(CallbackData, prefix='ref_links'):
    action: str
    link_name: Optional[str] = None


class ReferralLinkStates(StatesGroup):
    create = State()
    delete = State()


class Keyboards:

    @staticmethod
    def get_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Добавить ссылку', callback_data=ReferralLinksCallback(action='create'))
        builder.button(text='➖ Удалить ссылку', callback_data=ReferralLinksCallback(action='delete'))

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_cancel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Отменить', callback_data=ReferralLinksCallback(action='cancel'))
        return builder.as_markup()

    @staticmethod
    def get_links_to_delete_markup() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for n, link in enumerate(get_all_links()[:99], start=1):
            builder.button(
                text=f"❌ {n}) {link.name} : 👥 {link.user_count}",
                callback_data=ReferralLinksCallback(action='delete', link_name=link.name)
            )

        builder.button(text='🔙 Отменить', callback_data=ReferralLinksCallback(action='cancel'))
        builder.adjust(1)
        return builder.as_markup()


class Messages:
    @staticmethod
    def get_referral_links(bot_username: str) -> str:
        text = '🔗 Реферальные ссылки \n\n' \
               '<b>Список реферальных ссылок:</b> \n\n'

        for n, link in enumerate(get_all_links(), start=1):
            text += (
                f'{n} — <code>{link.name}</code> \n'
                f'🔗 <code>https://t.me/{bot_username}?start={link.name}</code> \n'
                f'📊 Кол-во переходов: {link.user_count} \n'
                f'📲 На ОП подписались: {link.passed_op_count} \n'
            )
            text += '-' * 30 + '\n'
        return text

    @staticmethod
    def select_link_to_delete():
        return '🔘 Нажмите на ссылку, которую хотите удалить: '


async def __handle_admin_reflinks_button(message: Message):
    bot_username = (await message.bot.get_me()).username
    text = Messages.get_referral_links(bot_username=bot_username)
    await message.answer(text=text, reply_markup=Keyboards.get_menu())


async def __handle_add_link_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        '🔘 Введите название. Можно использовать цифры и английские буквы:',
        reply_markup=Keyboards.get_cancel()
    )
    await state.set_state(ReferralLinkStates.create)


async def __handle_new_link_name(message: Message, state: FSMContext):
    if not message.text.isascii():
        await message.answer('❗В сообщении есть русские буквы. Попробуйте снова:', reply_markup=Keyboards.get_cancel())
    elif not message.text.isalnum():
        await message.answer('❗В сообщении есть символы. Попробуйте снова:', reply_markup=Keyboards.get_cancel())
    elif is_reflink_exists(message.text):
        await message.answer('❗Такая ссылка уже существует. Попробуйте снова:', reply_markup=Keyboards.get_cancel())
    else:
        create_reflink(message.text)
        bot_username = (await message.bot.get_me()).username
        await message.answer(
            '✅ Реферальная ссылка создана. \n\n'
            f'<u><i>Имя ссылки</i></u>: <code>{message.text}</code> \n'
            f'<u><i>Ссылка</i></u>: '
            f'<code>https://t.me/{bot_username}?start={message.text}</code>'
        )
        await state.clear()
        await __handle_admin_reflinks_button(message)


async def __handle_delete_link_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=Messages.select_link_to_delete(), reply_markup=Keyboards.get_links_to_delete_markup()
    )


async def __handle_link_to_delete_callback(callback: CallbackQuery, callback_data: ReferralLinksCallback):
    delete_reflink(callback_data.link_name)
    await callback.answer('✅ Ссылка удалена')

    await callback.message.edit_text(
        text=Messages.select_link_to_delete(),
        reply_markup=Keyboards.get_links_to_delete_markup()
    )


async def __handle_cancel_callback(callback: CallbackQuery, state: FSMContext):
    bot_username = (await callback.bot.get_me()).username
    text = Messages.get_referral_links(bot_username=bot_username)
    await callback.message.edit_text(
        text=text, reply_markup=Keyboards.get_menu()
    )
    await state.clear()


def register_reflinks_handlers(router: Router):
    router.message.register(__handle_admin_reflinks_button, F.text == '🔗 Реферальные ссылки 🔗')

    # отмена
    router.callback_query.register(__handle_cancel_callback, ReferralLinksCallback.filter(F.action == 'cancel'))

    # создание реферальной ссылки
    router.callback_query.register(__handle_add_link_callback, ReferralLinksCallback.filter(F.action == 'create'))
    router.message.register(__handle_new_link_name, ReferralLinkStates.create)

    # удаление реферальной ссылки
    router.callback_query.register(
        __handle_delete_link_callback, ReferralLinksCallback.filter((F.action == 'delete') & (~F.link_name))
    )
    router.callback_query.register(__handle_link_to_delete_callback, ReferralLinksCallback.filter(F.action == 'delete'))
