from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def add_delete_button(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    del_btn = InlineKeyboardButton('Delete', callback_data=f'delete')
    kb.add(del_btn)

    return kb
 

def commands_buttons(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    commands = InlineKeyboardButton('Commands', callback_data=f'commands')
    kb.add(commands)

    return kb


def main_menu(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)

    return kb


def sub_menu(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    main_menu = InlineKeyboardButton('Sub / Unsub', callback_data=f'sub_menu')
    kb.insert(main_menu)

    return kb


def profile_btn(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    profile_btn = InlineKeyboardButton('Profile', callback_data=f'profile')
    kb.add(profile_btn)

    return kb
