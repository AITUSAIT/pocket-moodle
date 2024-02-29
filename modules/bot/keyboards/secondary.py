from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def finish_adding_files_kb(kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton("Cancel", callback_data="convert_cancel")
    finish_adding = InlineKeyboardButton("Finish, Convert files", callback_data="convert_finish")
    kb.row(main_menu, finish_adding)

    return kb


def list_formats_kb(formats: list[str], kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for _ in formats:
        if index % 2 != 1:
            kb.insert(InlineKeyboardButton(_, callback_data=f"convert {_}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(_, callback_data=f"convert {_}"))
            else:
                kb.add(InlineKeyboardButton(_, callback_data=f"convert {_}"))
        index += 1

    main_menu = InlineKeyboardButton("Cancel", callback_data="convert_cancel")
    kb.row(main_menu)

    return kb


def list_dest_formats_kb(
    file_format: str, dest_formats: list[str], kb: InlineKeyboardMarkup = None
) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for _ in dest_formats:
        if index % 2 != 1:
            kb.insert(InlineKeyboardButton(_.upper(), callback_data=f"convert {file_format} {_.upper()}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(_.upper(), callback_data=f"convert {file_format} {_.upper()}"))
            else:
                kb.add(InlineKeyboardButton(_.upper(), callback_data=f"convert {file_format} {_.upper()}"))
        index += 1

    main_menu = InlineKeyboardButton("Back", callback_data="convert")
    kb.row(main_menu)

    return kb


def cancel_convert_kb(kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton("Cancel", callback_data="convert_cancel")
    kb.row(main_menu)

    return kb
