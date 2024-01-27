from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from modules.bot.functions.functions import convert_size, truncate_string
from modules.database import CourseContentDB
from modules.database.models import (Course, CourseContent,
                                     CourseContentModule,
                                     CourseContentModuleFile,
                                     CourseContentModuleUrl)


def back_btn(data: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    back = InlineKeyboardButton('Back', callback_data=data)
    kb.add(back)
    
    return kb


def active_courses_btns(courses: dict[str, Course], kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, course in courses.items():
        if index%2!=1:
            kb.insert(InlineKeyboardButton(course.name, callback_data=f"courses_contents {id}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(course.name, callback_data=f"courses_contents {id}"))
            else:
                kb.add(InlineKeyboardButton(course.name, callback_data=f"courses_contents {id}"))
        index += 1
    back = InlineKeyboardButton('Back', callback_data=f'main_menu')
    kb.add(back)
    
    return kb

def contents_btns(contents: dict[str, CourseContent], course_id: int, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, content in contents.items():
        state_skip = True
        for module in content.modules.values():
            if module.files != {} or module.urls != {}:
                state_skip = False
        if state_skip:
            continue
        
        if index%2!=1:
            kb.insert(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {id}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {id}"))
            else:
                kb.add(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {id}"))
        index += 1
    back = InlineKeyboardButton('Back', callback_data=f'courses_contents')
    kb.add(back)
    
    return kb


def modules_btns(modules: dict[str, CourseContentModule], course_id: int, content_id: int, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, module in modules.items():
        if module.files == {} and module.urls == {}:
            continue
        
        if index%2!=1:
            kb.insert(InlineKeyboardButton(module.name, callback_data=f"courses_contents {course_id} {content_id} {id}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(module.name, callback_data=f"courses_contents {course_id} {content_id} {id}"))
            else:
                kb.add(InlineKeyboardButton(module.name, callback_data=f"courses_contents {course_id} {content_id} {id}"))
        index += 1
    back = InlineKeyboardButton('Back', callback_data=f'courses_contents {course_id}')
    kb.add(back)
    
    return kb


def files_btns(files: dict[str, CourseContentModuleFile], kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    for file in files.values():
        kb.row(InlineKeyboardButton(f"{truncate_string(file.filename, 15)} ({convert_size(file.filesize)})", callback_data=f"courses_contents file {file.id}"))
    
    return kb


def url_btns(urls: dict[str, CourseContentModuleUrl], kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    for url in urls.values():
        kb.row(InlineKeyboardButton(f"{truncate_string(url.name, 20)}", url=url.url))
    
    return kb
