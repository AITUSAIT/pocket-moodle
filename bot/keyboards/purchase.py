from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)

from config import prices


def purchase_btn(kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    purchase_btn = InlineKeyboardButton('Purchase sub', callback_data=f'purchase')
    kb.row(main_menu, purchase_btn)

    return kb


def periods_btns(kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for key, value in prices.items():
        if index%2!=1:
            kb.insert(InlineKeyboardButton(f"{key} months - {value}тг", callback_data=f"purchase|{key}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(f"{key} month - {value}тг", callback_data=f"purchase|{key}"))
            else:
                kb.add(InlineKeyboardButton(f"{key} months - {value}тг", callback_data=f"purchase|{key}"))
        index+=1

    main_menu = InlineKeyboardButton('Back', callback_data=f'profile')
    kb.add(main_menu)

    return kb


def payment_btn(link: str, kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    purchase_btn = InlineKeyboardButton('Pay', url=link)
    kb.row(main_menu, purchase_btn)

    return kb
