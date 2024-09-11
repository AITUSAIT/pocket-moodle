from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_media_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Yes", callback_data="mailing add_media"),
        InlineKeyboardButton(text="No", callback_data="mailing no_media"),
    )

    return kb


def approve_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Approve", callback_data="mailing approve"),
        InlineKeyboardButton(text="Decline", callback_data="mailing decline"),
    )

    return kb
