from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def start_buttons(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('Get 1 free month', callback_data=f'demo')
    demo_btn = InlineKeyboardButton('Show all features', callback_data=f'commands')
    kb.row(purchase_btn, demo_btn)

    return kb
    