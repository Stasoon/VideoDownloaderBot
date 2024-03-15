from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject

from src.database.reflinks import increase_users_count
from src.keyboards.user import UserKeyboards
from src.messages.user import UserMessages
from src.database.users import create_user_if_not_exist


async def handle_start_command(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()

    user = message.from_user
    create_user_if_not_exist(
        telegram_id=user.id, firstname=user.first_name, username=user.username, reflink=command.args
    )

    increase_users_count(command.args)

    await message.answer(
        text=UserMessages.get_welcome(user_name=user.first_name),
        reply_markup=UserKeyboards.get_main_menu()
    )


def register_menu_handlers(router: Router):
    # Команда /start
    router.message.register(handle_start_command, CommandStart())
