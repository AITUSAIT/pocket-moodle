from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_delete_button(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    del_btn = InlineKeyboardButton(text="Delete", callback_data="delete")
    kb.add(del_btn)

    return kb


def commands_buttons(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    kb.button(text="Commands", callback_data="commands")

    return kb


def main_menu(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def profile_btn(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    settings_btn = InlineKeyboardButton(text="⚙️", callback_data="settings")
    profile_btn = InlineKeyboardButton(text="👤", callback_data="profile")
    kb.row(settings_btn, profile_btn)

    return kb
