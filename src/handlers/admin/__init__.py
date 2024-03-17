from aiogram import Router

from .admin_menu import register_admin_menu_handlers
from .edit_ads import register_edit_ads_handlers
from .necessary_subscriptions import register_necessary_subscriptions_handlers
from .statistic import register_admin_statistic_handlers
from .mailing import register_mailing_handlers
from .refferal_links import register_reflinks_handlers
from .admins_management import register_admin_management_handlers


def register_admin_handlers(router: Router):
    register_admin_menu_handlers(router)
    register_admin_statistic_handlers(router)
    register_reflinks_handlers(router)
    register_mailing_handlers(router)
    register_necessary_subscriptions_handlers(router)
    register_admin_management_handlers(router)
    register_edit_ads_handlers(router)
