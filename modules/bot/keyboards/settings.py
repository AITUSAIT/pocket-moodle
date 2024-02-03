from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from modules.database.models import SettingBot


def settings_btns(settings: SettingBot, kb: InlineKeyboardMarkup = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            f"Telegram Notifications {'🔔' if settings.status else '🔕'}",
            callback_data=f"settings status {0 if settings.status else 1}",
        )
    )

    if settings.status:
        kb.row(
            InlineKeyboardButton(
                f"Grades  {'🔔' if settings.notification_grade else '🔕'}",
                callback_data=f"settings notification_grade {0 if settings.notification_grade else 1}",
            ),
            InlineKeyboardButton(
                f"Deadlines  {'🔔' if settings.notification_deadline else '🔕'}",
                callback_data=f"settings notification_deadline {0 if settings.notification_deadline else 1}",
            ),
        )
    kb.row(InlineKeyboardButton("Back", callback_data="main_menu"))

    return kb
