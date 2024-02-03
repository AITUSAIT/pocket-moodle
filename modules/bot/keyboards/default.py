from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def add_delete_button(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    del_btn = InlineKeyboardButton("Delete", callback_data="delete")
    kb.add(del_btn)

    return kb


def commands_buttons(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    commands = InlineKeyboardButton("Commands", callback_data="commands")
    kb.insert(commands)

    return kb


def main_menu(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Back", callback_data="main_menu"))

    return kb


def profile_btn(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    settings_btn = InlineKeyboardButton("⚙️", callback_data="settings")
    profile_btn = InlineKeyboardButton("👤", callback_data="profile")
    kb.row(settings_btn, profile_btn)

    return kb
