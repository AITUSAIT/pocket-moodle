from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def register_self(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    reg_btn = InlineKeyboardButton("Register", callback_data="register")
    kb.add(reg_btn)

    return kb
