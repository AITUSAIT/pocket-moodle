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

    index = 0
    for format in formats:
        btn = InlineKeyboardButton(text=format, callback_data=f"convert {format}")
        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Cancel", callback_data="convert_cancel"))

    return kb


def list_dest_formats_kb(
    file_format: str, dest_formats: list[str], kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for dest_format in dest_formats:
        btn = InlineKeyboardButton(
            text=dest_format.upper(), callback_data=f"convert {file_format} {dest_format.upper()}"
        )

        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="convert"))

    return kb


def cancel_convert_kb(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Cancel", callback_data="convert_cancel"))

    return kb
