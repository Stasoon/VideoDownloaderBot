from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.admins import add_admin, delete_admin, is_admin_exist, get_admins


class AdminsManagementCallback(CallbackData, prefix='adm_management'):
    action: str
    admin_id: int = None


class AdminAddingStates(StatesGroup):
    wait_for_new_admin_id = State()
    wait_for_admin_to_delete_id = State()


class Keyboards:

    @staticmethod
    def get_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.button(text='➕ Добавить админа', callback_data=AdminsManagementCallback(action='add'))
        builder.button(text='➖ Исключить админа', callback_data=AdminsManagementCallback(action='delete'))

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_cancel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Отменить', callback_data=AdminsManagementCallback(action='cancel'))
        return builder.as_markup()


class Messages:
    @staticmethod
    def get_admins() -> str:
        text = '👤 Управление админами 👤 \n\n' \
               '<b>White-лист администраторских ID:</b> \n\n'
        for n, admin in enumerate(get_admins(), start=1):
            text += f'{n}) <code>{admin.telegram_id}</code> - <a href="tg://user?id={admin.telegram_id}">[ссылка]</a> \n'
        return text


async def __handle_admin_management_button(message: Message):
    await message.answer(Messages.get_admins(), reply_markup=Keyboards.get_menu())


async def __handle_add_admin_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text='🔘 Получите id человека в боте @getmyid_bot. \nЗатем пришлите его сюда',
        reply_markup=Keyboards.get_cancel()
    )
    await state.set_state(AdminAddingStates.wait_for_new_admin_id)


async def __handle_new_admins_message(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            text='❗id не может содержать букв! Попробуйте снова:',
            reply_markup=Keyboards.get_cancel()
        )
        return

    await state.clear()

    if is_admin_exist(int(message.text)):
        await message.answer(
            '❗ Этот человек уже является админом!',
            reply_markup=Keyboards.get_cancel()
        )
        await __handle_admin_management_button(message)
        return

    add_admin(telegram_id=int(message.text), admin_name='Админ')
    await message.answer('✅ Админ добавлен')
    await __handle_admin_management_button(message)


async def __handle_delete_admin_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        text='🔘 Пришлите мне id админа, которого хотите исключить:',
        reply_markup=Keyboards.get_cancel()
    )
    await state.set_state(AdminAddingStates.wait_for_admin_to_delete_id)


async def __handle_admin_to_delete_id(message: Message, state: FSMContext):
    if delete_admin(int(message.text)):
        await message.answer('✅ Админ исключён!')
        await state.clear()
        await __handle_admin_management_button(message)
    else:
        await message.answer(
            text='❗Админа с таким id не существует. Попробуйте снова:',
            reply_markup=Keyboards.get_cancel()
        )


async def __handle_cancel_management_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await callback.message.answer(Messages.get_admins(), reply_markup=Keyboards.get_menu())


def register_admin_management_handlers(router: Router):
    router.message.register(__handle_admin_management_button, F.text == '👤 Управление админами 👤')

    # добавление
    router.callback_query.register(
        __handle_add_admin_callback,
        AdminsManagementCallback.filter(F.action == 'add'),
    )
    router.message.register(
        __handle_new_admins_message,
        AdminAddingStates.wait_for_new_admin_id,
    )

    # удаление
    router.callback_query.register(
        __handle_delete_admin_callback,
        AdminsManagementCallback.filter(F.action == 'delete'),
    )

    router.message.register(
        __handle_admin_to_delete_id,
        AdminAddingStates.wait_for_admin_to_delete_id
    )

    # отмена
    router.callback_query.register(
        __handle_cancel_management_callback,
        AdminsManagementCallback.filter(F.action == 'cancel'),
    )



