import asyncio
from typing import Any, Coroutine

import async_lru
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.bot.functions.functions import convert_size, truncate_string_in_center
from modules.pm_api.api import PocketMoodleAPI
from modules.pm_api.models import (
    Course,
    CourseContent,
    CourseContentModule,
    CourseContentModuleFile,
    CourseContentModuleUrl,
)


@async_lru.alru_cache(ttl=120)
async def __get_module_data(
    course_id: int,
    content_id: int | None = None,
) -> tuple[list[dict[str, CourseContentModuleFile]], list[dict[str, CourseContentModuleUrl]]]:
    files_tasks: list[Coroutine[Any, Any, dict[str, CourseContentModuleFile]]] = []
    urls_tasks: list[Coroutine[Any, Any, dict[str, CourseContentModuleUrl]]] = []
    course_contents = await PocketMoodleAPI().get_course_contents(int(course_id))
    if not content_id:
        for course_content in course_contents.values():
            # Create tasks for fetching files and URLs concurrently
            for module in course_content.modules.values():
                files_tasks.append(PocketMoodleAPI().get_course_content_module_files(course_id, module.id))
                urls_tasks.append(PocketMoodleAPI().get_course_content_module_urls(course_id, module.id))
    else:
        course_content = course_contents[str(content_id)]
        # Create tasks for fetching files and URLs concurrently
        for module in course_content.modules.values():
            files_tasks.append(PocketMoodleAPI().get_course_content_module_files(course_id, module.id))
            urls_tasks.append(PocketMoodleAPI().get_course_content_module_urls(course_id, module.id))

    # Wait for all tasks to complete
    files_results: list[dict[str, CourseContentModuleFile]] = await asyncio.gather(*files_tasks)
    urls_results: list[dict[str, CourseContentModuleUrl]] = await asyncio.gather(*urls_tasks)

    return files_results, urls_results


def back_btn(data: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Back", callback_data=data))

    return kb


async def active_courses_btns(
    courses: dict[str, Course], kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for course_id, course in courses.items():
        state_skip = True
        files_results, urls_results = await __get_module_data(course_id)

        if not all(not files and not urls for files, urls in zip(files_results, urls_results)):
            state_skip = False
        if state_skip:
            continue

        btn = InlineKeyboardButton(text=course.name, callback_data=f"courses_contents {course_id}")
        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


async def contents_btns(
    contents: dict[str, CourseContent], course_id: int, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for content_id, content in contents.items():
        files_results, urls_results = await __get_module_data(course_id, content_id)
        if all(not files and not urls for files, urls in zip(files_results, urls_results)):
            continue

        btn = InlineKeyboardButton(text=content.name, callback_data=f"courses_contents {course_id} {content_id}")

        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="courses_contents"))

    return kb


async def modules_btns(
    modules: dict[str, CourseContentModule], course_id: int, content_id: int, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for module_id, module in modules.items():
        files = await PocketMoodleAPI().get_course_content_module_files(course_id, module.id)
        urls = await PocketMoodleAPI().get_course_content_module_urls(course_id, module.id)
        if files == {} and urls == {}:
            continue

        btn = InlineKeyboardButton(
            text=module.name, callback_data=f"courses_contents {course_id} {content_id} {module_id}"
        )
        if len(files) == 1 and len(urls) == 0:
            file = list(files.values())[0]
            btn = InlineKeyboardButton(
                text=f"{truncate_string_in_center(file.filename, 40)} ({convert_size(file.filesize)})",
                callback_data=f"courses_contents file {course_id} {module_id} {file.id}",
            )
        elif len(files) == 0 and len(urls) == 1:
            url = list(urls.values())[0]
            btn = InlineKeyboardButton(text=f"{truncate_string_in_center(url.name, 40)}", url=url.url)

        kb.row(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data=f"courses_contents {course_id}"))

    return kb


def files_btns(
    files: dict[str, CourseContentModuleFile], course_id: int, module_id: int, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for file in files.values():
        kb.row(
            InlineKeyboardButton(
                text=f"{truncate_string_in_center(file.filename, 40)} ({convert_size(file.filesize)})",
                callback_data=f"courses_contents file {course_id} {module_id} {file.id}",
            )
        )

    return kb


def url_btns(urls: dict[str, CourseContentModuleUrl], kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for url in urls.values():
        kb.row(InlineKeyboardButton(text=f"{truncate_string_in_center(url.name, 40)}", url=url.url))

    return kb
