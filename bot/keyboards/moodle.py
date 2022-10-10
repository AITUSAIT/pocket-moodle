from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def register_moodle_query(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('Register Moodle account', callback_data=f'register_moodle')
    kb.add(purchase_btn)

    return kb


def add_grades_deadlines_btns(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    grades_btn = InlineKeyboardButton('Get grades', callback_data=f'get_grades')
    deadlines_btn = InlineKeyboardButton('Get deadlines', callback_data=f'get_deadlines')
    gpa_btn = InlineKeyboardButton('Get GPA', callback_data=f'get_gpa')
    att_btn = InlineKeyboardButton('Get Attendance', callback_data=f'get_att')
    kb.row(grades_btn, deadlines_btn)
    kb.add(gpa_btn)
    kb.add(att_btn)

    return kb


def sub_buttons(sub_grades, sub_deadlines, kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    if not sub_grades:
        grades_btn = InlineKeyboardButton('Sub grades', callback_data=f'sub_grades 1')
    else:
        grades_btn = InlineKeyboardButton('Unsub grades', callback_data=f'sub_grades 0')
    if not sub_deadlines:
        deadlines_btn = InlineKeyboardButton('Sub deadlines', callback_data=f'sub_deadlines 1')
    else:
        deadlines_btn = InlineKeyboardButton('Unsub deadlines', callback_data=f'sub_deadlines 0')
    kb.row(grades_btn, deadlines_btn)
    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def grades_btns(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    grades_btn_active = InlineKeyboardButton('Only active courses', callback_data=f'get_grades active')
    grades_btn_all = InlineKeyboardButton('All courses', callback_data=f'get_grades all')
    kb.row(grades_btn_active, grades_btn_all)
    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def deadlines_btns(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()

    filters = {
        '<1 day': 'get_deadlines 1',
        '<2 days': 'get_deadlines 2',
        '<5 days': 'get_deadlines 5',
        '<10 days': 'get_deadlines 10',
        '<15 days': 'get_deadlines 15',
        'All': 'get_deadlines 90',
    }
    
    for index in range(0, len(filters), 2):
        if index+1 >= len(filters):
            kb.add(InlineKeyboardButton(list(filters.keys())[index], callback_data=list(filters.values())[index]))
        else:
            kb.row(
                InlineKeyboardButton(list(filters.keys())[index], callback_data=list(filters.values())[index]),
                InlineKeyboardButton(list(filters.keys())[index+1], callback_data=list(filters.values())[index+1])
            )

    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def att_btns(kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    att_btn_active = InlineKeyboardButton('Only active courses', callback_data=f'get_att active')
    att_btn_total = InlineKeyboardButton('Total', callback_data=f'get_att total')
    kb.row(att_btn_active, att_btn_total)
    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def active_att_btns(courses, kb: types.inline_keyboard = None):
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, course in courses.items():
        if course['active']:
            if index%2!=1:
                kb.insert(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
            else:
                if index == 1:
                    kb.insert(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
                else:
                    kb.add(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
    main_menu = InlineKeyboardButton('Back to main menu', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb
