from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.bot.functions.functions import convert_size, truncate_string
from modules.database.models import (
    Course,
    CourseContent,
    CourseContentModule,
    CourseContentModuleFile,
    CourseContentModuleUrl,
)


def back_btn(data: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    back = InlineKeyboardButton(text="Back", callback_data=data)
    kb.add(back)

    return kb


def active_courses_btns(courses: dict[str, Course], kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for course_id, course in courses.items():
        if index % 2 != 1:
            kb.button(text=course.name, callback_data=f"courses_contents {course_id}")
        else:
            if index == 1:
                kb.button(text=course.name, callback_data=f"courses_contents {course_id}")
            else:
                kb.add(InlineKeyboardButton(text=course.name, callback_data=f"courses_contents {course_id}"))
        index += 1
    back = InlineKeyboardButton(text="Back", callback_data="main_menu")
    kb.add(back)

    return kb


def contents_btns(
    contents: dict[str, CourseContent], course_id: int, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for content_id, content in contents.items():
        state_skip = True
        for module in content.modules.values():
            if module.files != {} or module.urls != {}:
                state_skip = False
        if state_skip:
            continue

        if index % 2 != 1:
            kb.button(text=content.name, callback_data=f"courses_contents {course_id} {content_id}")
        else:
            if index == 1:
                kb.button(text=content.name, callback_data=f"courses_contents {course_id} {content_id}")
            else:
                kb.add(
                    InlineKeyboardButton(text=content.name, callback_data=f"courses_contents {course_id} {content_id}")
                )
        index += 1
    back = InlineKeyboardButton(text="Back", callback_data="courses_contents")
    kb.add(back)

    return kb


def modules_btns(
    modules: dict[str, CourseContentModule], course_id: int, content_id: int, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 1
    for module_id, module in modules.items():
        if module.files == {} and module.urls == {}:
            continue

        if index % 2 != 1:
            kb.button(text=module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}")
        else:
            if index == 1:
                kb.button(text=module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}")
            else:
                kb.add(
                    InlineKeyboardButton(
                        text=module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}"
                    )
                )
        index += 1
    back = InlineKeyboardButton(text="Back", callback_data=f"courses_contents {course_id}")
    kb.add(back)

    return kb


def files_btns(
    files: dict[str, CourseContentModuleFile], kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for file in files.values():
        kb.row(
            InlineKeyboardButton(
                text=f"{truncate_string(file.filename, 15)} ({convert_size(file.filesize)})",
                callback_data=f"courses_contents file {file.id}",
            )
        )

    return kb


def url_btns(urls: dict[str, CourseContentModuleUrl], kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for url in urls.values():
        kb.row(InlineKeyboardButton(text=f"{truncate_string(url.name, 20)}", url=url.url))

    return kb
