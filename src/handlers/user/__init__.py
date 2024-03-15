from aiogram import Router

from .menu import register_menu_handlers
from .links import register_links_handlers
from .not_subscribers import register_not_subs_handlers


def register_user_handlers(router: Router):
    menu_router = Router()
    register_menu_handlers(menu_router)

    links_router = Router()
    register_links_handlers(links_router)

    not_subs_router = Router()
    register_not_subs_handlers(not_subs_router)

    router.include_routers(menu_router, links_router, not_subs_router)
