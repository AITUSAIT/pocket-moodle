from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def start_buttons(kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('Get 1 free month', callback_data=f'demo')
    demo_btn = InlineKeyboardButton('Show all features', callback_data=f'commands')
    kb.row(purchase_btn, demo_btn)

    return kb


def periods_btns(kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('1 month - 480тг', callback_data=f'purchase|1')
    kb.add(purchase_btn)

    return kb


def payment_btn(link: str, kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('Pay', url=link)
    kb.add(purchase_btn)

    return kb
