from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def finish_adding_files_kb(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    main_menu = InlineKeyboardButton(text="Cancel", callback_data="convert_cancel")
    finish_adding = InlineKeyboardButton(text="Finish, Convert files", callback_data="convert_finish")
    kb.row(main_menu, finish_adding)

    return kb


def list_formats_kb(formats: list[str], kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for _ in formats:
        if index % 2 != 1:
            kb.button(text=_, callback_data=f"convert {_}")
        else:
            if index == 1:
                kb.button(text=_, callback_data=f"convert {_}")
            else:
                kb.add(InlineKeyboardButton(text=_, callback_data=f"convert {_}"))
        index += 1

    main_menu = InlineKeyboardButton(text="Cancel", callback_data="convert_cancel")
    kb.row(main_menu)

    return kb


def list_dest_formats_kb(
    file_format: str, dest_formats: list[str], kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for _ in dest_formats:
        if index % 2 != 1:
            kb.button(text=_.upper(), callback_data=f"convert {file_format} {_.upper()}")
        else:
            if index == 1:
                kb.button(text=_.upper(), callback_data=f"convert {file_format} {_.upper()}")
            else:
                kb.add(InlineKeyboardButton(text=_.upper(), callback_data=f"convert {file_format} {_.upper()}"))
        index += 1

    main_menu = InlineKeyboardButton(text="Back", callback_data="convert")
    kb.row(main_menu)

    return kb


def cancel_convert_kb(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    main_menu = InlineKeyboardButton(text="Cancel", callback_data="convert_cancel")
    kb.row(main_menu)

    return kb
