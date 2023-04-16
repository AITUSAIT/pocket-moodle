from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)

from config import prices


def profile_btns(kb: InlineKeyboardMarkup = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    settings = InlineKeyboardButton('Settings', callback_data=f'settings')
    purchase_btn = InlineKeyboardButton('Purchase sub', callback_data=f'purchase_sub')
    promocode_btn = InlineKeyboardButton('Purchase promocode', callback_data=f'purchase_promo')
    kb.row(settings)
    kb.row(purchase_btn, promocode_btn)
    kb.row(main_menu)

    return kb


def purchase_btns(kb: InlineKeyboardMarkup = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    purchase_btn = InlineKeyboardButton('Purchase sub', callback_data=f'purchase_sub')
    promocode_btn = InlineKeyboardButton('Purchase promocode', callback_data=f'purchase_promo')
    kb.add(purchase_btn)
    kb.add(promocode_btn)

    return kb


def periods_btns(is_for_promocode: bool, kb: InlineKeyboardMarkup = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    f = "purchase_sub" if not is_for_promocode else "purchase_promo"
    index = 1
    for key, value in prices.items():
        if index%2!=1:
            kb.insert(InlineKeyboardButton(f"{key} months - {value}$", callback_data=f"{f}|{key}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(f"{key} month - {value}$", callback_data=f"{f}|{key}"))
            else:
                kb.add(InlineKeyboardButton(f"{key} months - {value}$", callback_data=f"{f}|{key}"))
        index+=1

    main_menu = InlineKeyboardButton('Back', callback_data=f'purchase')
    kb.add(main_menu)

    return kb


def payment_btn(link: str, kb: InlineKeyboardMarkup = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    purchase_btn = InlineKeyboardButton('Pay', url=link)
    kb.row(purchase_btn)
    return kb
