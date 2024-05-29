from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb
