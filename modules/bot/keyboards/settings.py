from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.pm_api.models import SettingBot


def settings_btns(settings: SettingBot, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(
            text=f"Telegram Notifications {'🔔' if settings.status else '🔕'}",
            callback_data=f"settings status {0 if settings.status else 1}",
        )
    )

    if settings.status:
        kb.row(
            InlineKeyboardButton(
                text=f"Grades  {'🔔' if settings.notification_grade else '🔕'}",
                callback_data=f"settings notification_grade {0 if settings.notification_grade else 1}",
            ),
            InlineKeyboardButton(
                text=f"Deadlines  {'🔔' if settings.notification_deadline else '🔕'}",
                callback_data=f"settings notification_deadline {0 if settings.notification_deadline else 1}",
            ),
        )
    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb
