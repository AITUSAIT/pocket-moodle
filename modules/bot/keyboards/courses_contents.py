from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from modules.bot.functions.functions import convert_size, truncate_string
from modules.database.models import (
    Course,
    CourseContent,
    CourseContentModule,
    CourseContentModuleFile,
    CourseContentModuleUrl,
)


def back_btn(data: str, kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    back = InlineKeyboardButton("Back", callback_data=data)
    kb.add(back)

    return kb


def active_courses_btns(courses: dict[str, Course], kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for course_id, course in courses.items():
        if index % 2 != 1:
            kb.insert(InlineKeyboardButton(course.name, callback_data=f"courses_contents {course_id}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(course.name, callback_data=f"courses_contents {course_id}"))
            else:
                kb.add(InlineKeyboardButton(course.name, callback_data=f"courses_contents {course_id}"))
        index += 1
    back = InlineKeyboardButton("Back", callback_data="main_menu")
    kb.add(back)

    return kb


def contents_btns(
    contents: dict[str, CourseContent], course_id: int, kb: InlineKeyboardMarkup = None
) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for content_id, content in contents.items():
        state_skip = True
        for module in content.modules.values():
            if module.files != {} or module.urls != {}:
                state_skip = False
        if state_skip:
            continue

        if index % 2 != 1:
            kb.insert(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {content_id}"))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {content_id}"))
            else:
                kb.add(InlineKeyboardButton(content.name, callback_data=f"courses_contents {course_id} {content_id}"))
        index += 1
    back = InlineKeyboardButton("Back", callback_data="courses_contents")
    kb.add(back)

    return kb


def modules_btns(
    modules: dict[str, CourseContentModule], course_id: int, content_id: int, kb: InlineKeyboardMarkup = None
) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    index = 1
    for module_id, module in modules.items():
        if module.files == {} and module.urls == {}:
            continue

        if index % 2 != 1:
            kb.insert(
                InlineKeyboardButton(module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}")
            )
        else:
            if index == 1:
                kb.insert(
                    InlineKeyboardButton(
                        module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}"
                    )
                )
            else:
                kb.add(
                    InlineKeyboardButton(
                        module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}"
                    )
                )
        index += 1
    back = InlineKeyboardButton("Back", callback_data=f"courses_contents {course_id}")
    kb.add(back)

    return kb


def files_btns(files: dict[str, CourseContentModuleFile], kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    for file in files.values():
        kb.row(
            InlineKeyboardButton(
                f"{truncate_string(file.filename, 15)} ({convert_size(file.filesize)})",
                callback_data=f"courses_contents file {file.id}",
            )
        )

    return kb


def url_btns(urls: dict[str, CourseContentModuleUrl], kb: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    if kb is None:
        kb = InlineKeyboardMarkup()

    for url in urls.values():
        kb.row(InlineKeyboardButton(f"{truncate_string(url.name, 20)}", url=url.url))

    return kb
