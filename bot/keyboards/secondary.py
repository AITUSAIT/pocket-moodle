from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def finish_adding_photos(kb: InlineKeyboardMarkup = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    main_menu = InlineKeyboardButton('Cancel', callback_data=f'main_menu')
    finish_adding = InlineKeyboardButton('Finish adding photos', callback_data=f'finish photos')
    kb.row(main_menu, finish_adding)

    return kb

