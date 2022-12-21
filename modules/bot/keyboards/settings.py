from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def settings_btns(sleep_status, calendar_notify, kb: InlineKeyboardMarkup = None)  -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    back = InlineKeyboardButton('Back', callback_data=f'profile')

    if not sleep_status:
        sleep_awake_btn = InlineKeyboardButton('Updates ✅', callback_data=f'sleep')
    else:
        sleep_awake_btn = InlineKeyboardButton('Updates ❌', callback_data=f'awake')
    
    if not calendar_notify:
        calendar_notify_btn = InlineKeyboardButton('Calendar notify ❌', callback_data=f'calendar_notify 1')
    else:
        calendar_notify_btn = InlineKeyboardButton('Calendar notify ✅', callback_data=f'calendar_notify 0')
    
    kb.row(sleep_awake_btn, calendar_notify_btn)
    kb.row(back)

    return kb