from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.pm_api.models import MailingSettings


def settings_btns(settings: MailingSettings, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.max_width = 2

    kb.add(
        InlineKeyboardButton(
            text=f"aitusa_events {'🔔' if settings.aitusa_event else '🔕'}",
            callback_data=f"mailing_settings aitusa_event {0 if settings.aitusa_event else 1}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=f"club_events {'🔔' if settings.club_event else '🔕'}",
            callback_data=f"mailing_settings club_event {0 if settings.club_event else 1}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=f"scientific_events {'🔔' if settings.scientific_event else '🔕'}",
            callback_data=f"mailing_settings scientific_event {0 if settings.scientific_event else 1}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=f"cooperations {'🔔' if settings.cooperation else '🔕'}",
            callback_data=f"mailing_settings cooperation {0 if settings.cooperation else 1}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=f"vacancies {'🔔' if settings.vacancy else '🔕'}",
            callback_data=f"mailing_settings vacancy {0 if settings.vacancy else 1}",
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=f"academ_mobilities {'🔔' if settings.academ_mobility else '🔕'}",
            callback_data=f"mailing_settings academ_mobility {0 if settings.academ_mobility else 1}",
        )
    )

    return kb
