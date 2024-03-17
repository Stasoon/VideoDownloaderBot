import json
from typing import Optional, Literal

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import advertisements
from src.database.models import Advertisement
from src.keyboards.admin import MailingKb


class AdvertisementAdding(StatesGroup):
    wait_for_content_message = State()
    add_preview = State()
    wait_for_markup_data = State()
    wait_for_confirm = State()


class Messages:
    @staticmethod
    def ask_for_post_content():
        return "Пришлите <u>текст</u> поста, который хотите разослать. Добавьте нужные <u>медиа-файлы</u>"

    @staticmethod
    def get_button_data_incorrect():
        return 'Отправленная информация не верна. ' \
               'Пожалуйста, в первой строке напишите название кнопки, во второй - ссылку.'

    @staticmethod
    def prepare_post():
        return "<i>Итоговый вид рекламы:</i>"

    @staticmethod
    def get_mailing_canceled():
        return '⛔ Добавление рекламы отменено'

    @staticmethod
    def get_markup_adding_manual():
        return '''Отправьте боту название кнопки и адрес ссылки. Например, так: \n
Telegram telegram.org \n
Чтобы отправить несколько кнопок за раз, используйте разделитель «|». Каждый новый ряд – с новой строки. 
Например, так: \n
Telegram telegram.org | Новости telegram.org/blog
FAQ telegram.org/faq | Скачать telegram.org/apps'''

    @staticmethod
    def ask_about_save_ad():
        return "<u><b>Сохранить рекламу?</b></u>"


class DeleteAdCallback(CallbackData, prefix='delete_ad'):
    ad_id: int


class AppendPreviewCallback(CallbackData, prefix='preview'):
    action: Literal['T', 'F']
    ad_id: Optional[int] = None


class Keyboards:

    @staticmethod
    def __get_inline_kb_from_json(ad: Advertisement) -> InlineKeyboardMarkup:
        """ Из словаря с клавиатурой делает объект """
        markup = json.loads(ad.markup_json)
        inline_kb = []

        for row in markup:
            a = []
            inline_kb.append(a)
            for b in row:
                a.append(InlineKeyboardButton(text=b.get('text'), url=b.get('url')))

        return InlineKeyboardMarkup(inline_keyboard=inline_kb)

    @staticmethod
    def get_add_advertisement() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='➕', callback_data='add_advertisement')
        return builder.as_markup()

    @staticmethod
    def get_ad_actions_markup(ad: Advertisement) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        if ad.markup_json is None:
            markup = None
        else:
            markup = Keyboards.__get_inline_kb_from_json(ad=ad)

        act = 'T' if ad.show_preview else 'F'
        builder.button(
            text=f"Превью: {'✅' if ad.show_preview else '❌'}",
            callback_data=AppendPreviewCallback(action=act, ad_id=ad.id)
        )
        builder.button(text='❌ Удалить ❌', callback_data=DeleteAdCallback(ad_id=ad.id))
        return markup

    @staticmethod
    def get_ask_about_preview():
        builder = InlineKeyboardBuilder()
        builder.button(text='Да', callback_data=AppendPreviewCallback(action='T'))
        builder.button(text='Нет', callback_data=AppendPreviewCallback(action='F'))
        return builder.as_markup()

    @staticmethod
    def add_button():
        builder = InlineKeyboardBuilder()
        builder.button(text='Продолжить без кнопки', callback_data='save_ad_wout_button')
        return builder.as_markup()

    @staticmethod
    def get_save():
        builder = InlineKeyboardBuilder()
        builder.button(text='💾 Сохранить 💾', callback_data='save_ad')
        return builder.as_markup()

    @staticmethod
    def get_save_or_cancel():
        builder = InlineKeyboardBuilder()

        builder.button(text='💾 Сохранить 💾', callback_data='save_ad')
        builder.button(text='🔙 Отменить', callback_data='cancel_ad_creating')

        builder.adjust(1)
        return builder.as_markup()


async def __handle_admin_ad_shows_button(message: Message):
    await message.answer(text='📄 Показы рекламы 📄', reply_markup=Keyboards.get_add_advertisement())
    for ad in advertisements.get_active_ads():
        text = f"{ad.text} \n\nПоказано раз: {ad.showed_count}"
        markup = Keyboards.get_ad_actions_markup(ad)
        await message.answer(text=text, reply_markup=markup, parse_mode='HTML')


async def __handle_toggle_show_preview(callback: CallbackQuery, callback_data: AppendPreviewCallback):
    ad = advertisements.get_ad_by_id(ad_id=int(callback_data.ad_id))
    if not ad:
        await callback.message.delete()
        return

    show_preview = True if callback_data.get('action') == 'True' else False
    ad = advertisements.change_show_preview(advertisement=ad, show_preview=show_preview)

    text = f"{ad.text} \n\nПоказано раз: {ad.showed_count}"
    markup = Keyboards.get_ad_actions_markup(ad)
    await callback.message.edit_text(text=text, reply_markup=markup, disable_web_page_preview=not show_preview)


async def __handle_delete_advertisement_callback(
        callback: CallbackQuery, callback_data: DeleteAdCallback
):
    ad_id = callback_data.ad_id
    advertisements.delete_ad(advertisement_id=ad_id)
    await callback.message.delete()


async def __handle_add_advertisement_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(AdvertisementAdding.wait_for_content_message.state)
    await callback.message.answer('✏ Пришлите рекламный текст:')


async def __handle_new_advertisement_content_message(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)

    await message.answer(text='Добавлять превью?', reply_markup=Keyboards.get_ask_about_preview())
    await state.set_state(AdvertisementAdding.add_preview.state)


async def __handle_add_preview_callback(
        callback: CallbackQuery, callback_data: AppendPreviewCallback, state: FSMContext
):
    await callback.message.delete()
    await state.update_data(append_preview=callback_data.action)

    await callback.message.answer(
        text=Messages.get_markup_adding_manual(),
        reply_markup=Keyboards.add_button(),
        disable_web_page_preview=True
    )
    await state.set_state(AdvertisementAdding.wait_for_markup_data.state)


async def __handle_url_button_data(message: Message, state: FSMContext):
    state_data = await state.get_data()
    markup = MailingKb.generate_markup_from_text(message.text)

    try:
        await message.answer(text=state_data.get('text'), reply_markup=markup)
    except Exception:
        await message.answer(
            'Вы ввели неправильную информацию для кнопки. Попробуйте снова:',
            reply_markup=Keyboards.add_button()
        )
        return

    bttns = []
    for row in markup.inline_keyboard:
        r = []
        bttns.append(r)
        for b in row:
            r.append({'text': b.text, 'url': b.url})

    d = json.dumps(bttns)
    await state.update_data(markup=d)
    await message.answer(Messages.ask_about_save_ad(), reply_markup=Keyboards.get_save_or_cancel())
    await state.set_state(AdvertisementAdding.wait_for_confirm.state)


async def __handle_continue_wout_button_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()

    markup_json = data.get('markup')
    markup = InlineKeyboardMarkup.to_object(markup_json) if markup_json else None
    show_preview = True if data.get('append_preview') == 'True' else False

    await callback.message.answer(Messages.prepare_post())
    await callback.message.answer(
        text=data.get('text'), reply_markup=markup, disable_web_page_preview=not show_preview
    )

    await callback.message.answer(Messages.ask_about_save_ad(), reply_markup=Keyboards.get_save_or_cancel())
    await state.set_state(AdvertisementAdding.wait_for_confirm.state)


async def __handle_save_ad_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    await state.clear()

    show_preview = True if data.get('append_preview') == 'T' else False
    advertisements.create_ad(
        text=data.get('text'), markup_json=data.get('markup'), show_preview=show_preview
    )

    await callback.message.answer('✅ Сохранено')
    await __handle_admin_ad_shows_button(callback.message)


async def __handle_ad_creating_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(Messages.get_mailing_canceled())
    await state.clear()


def register_edit_ads_handlers(router: Router):
    # Кнопка из меню
    router.message.register(__handle_admin_ad_shows_button, F.text == '📄 Показы рекламы 📄')

    # Добавление рекламы
    router.callback_query.register(
        __handle_add_advertisement_callback, F.data == 'add_advertisement'
    )

    # Сообщение с текстом новой рекламы
    router.message.register(
        __handle_new_advertisement_content_message, AdvertisementAdding.wait_for_content_message
    )

    # Показывать превью? (при создании)
    router.callback_query.register(
        __handle_add_preview_callback,
        AppendPreviewCallback.filter(),
        AdvertisementAdding.add_preview,
    )

    # обработка содержимого для url-кнопки
    router.message.register(
        __handle_url_button_data, AdvertisementAdding.wait_for_markup_data
    )

    # обработка калбэка продолжения без url-кнопки
    router.callback_query.register(
        __handle_continue_wout_button_callback, AdvertisementAdding.wait_for_markup_data,
    )

    # обработка калбэка подтверждения сохранения рекламы
    router.callback_query.register(
        __handle_save_ad_callback, F.data == 'save_ad', AdvertisementAdding.wait_for_confirm
    )

    # обработка отмены создания рекламы
    router.callback_query.register(__handle_ad_creating_callback, F.data == "cancel_ad_creating")

    # Удаление рекламы
    router.callback_query.register(
        __handle_delete_advertisement_callback, DeleteAdCallback.filter()
    )

    router.callback_query.register(__handle_toggle_show_preview, AppendPreviewCallback.filter())
