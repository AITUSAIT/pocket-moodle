from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_btns(kb: InlineKeyboardMarkup | None = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton("Back", callback_data="main_menu")
    kb.row(main_menu)

    return kb
