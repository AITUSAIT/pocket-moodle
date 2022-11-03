from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)

from config import prices


def profile_btns(sleep_status, kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    if not sleep_status:
        sleep_awake_btn = InlineKeyboardButton('Sleep', callback_data=f'sleep')
    else:
        sleep_awake_btn = InlineKeyboardButton('Awake', callback_data=f'awake')
    purchase_btn = InlineKeyboardButton('Purchase sub', callback_data=f'purchase')
    kb.row(main_menu, sleep_awake_btn, purchase_btn)

    return kb


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


def payment_btn(link: str, inv_id, signa, kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    purchase_btn = InlineKeyboardButton('Pay', url=link)
    check_btn = InlineKeyboardButton('Check payment', callback_data=f'check_payment {inv_id} {signa}')
    kb.row(purchase_btn)
    kb.row(check_btn)

    return kb
