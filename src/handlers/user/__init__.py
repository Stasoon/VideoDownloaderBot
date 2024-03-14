from aiogram import Router

from .menu import register_menu_handlers
from .links import register_links_handlers


def register_user_handlers(router: Router):
    register_menu_handlers(router)
    register_links_handlers(router)
