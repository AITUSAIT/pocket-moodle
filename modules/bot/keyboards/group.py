from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def register_self(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    reg_btn = InlineKeyboardButton(text="Register", callback_data="register")
    kb.add(reg_btn)

    return kb
