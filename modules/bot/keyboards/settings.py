from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def settings_btns(sleep_status, kb: InlineKeyboardMarkup = None)  -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    back = InlineKeyboardButton('Back', callback_data=f'profile')

    if not sleep_status:
        sleep_awake_btn = InlineKeyboardButton('Sleep updates', callback_data=f'sleep')
    else:
        sleep_awake_btn = InlineKeyboardButton('Awake updates', callback_data=f'awake')
    
    kb.row(sleep_awake_btn)
    kb.row(back)

    return kb