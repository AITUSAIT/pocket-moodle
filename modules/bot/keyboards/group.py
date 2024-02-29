from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def register_self(kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()
    reg_btn = InlineKeyboardButton("Register", callback_data="register")
    kb.add(reg_btn)

    return kb
