from aiogram import Dispatcher, F, types
from aiogram.enums.chat_action import ChatAction

import global_vars
from modules.bot.functions.rights import login_required
from modules.bot.keyboards.courses_contents import (
    active_courses_btns,
    back_btn,
    contents_btns,
    files_btns,
    modules_btns,
    url_btns,
)
from modules.bot.throttling import rate_limit
from modules.database import CourseContentDB, CourseDB
from modules.logger import Logger


@rate_limit(limit=1)
@Logger.log_msg
@login_required
async def courses_contents(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id

    courses = await CourseDB.get_courses(user_id=user_id, is_active=True)

    await query.message.edit_text("Choose:", reply_markup=active_courses_btns(courses=courses).as_markup())


@rate_limit(limit=1)
@Logger.log_msg
@login_required
async def courses_contents_course(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    course_id = int(query.data.split()[-1])

    course_content = await CourseContentDB.get_course_contents(course_id=course_id)

    await query.message.edit_reply_markup(reply_markup=contents_btns(course_content, course_id=course_id).as_markup())


@rate_limit(limit=1)
@Logger.log_msg
@login_required
async def courses_contents_course_content(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    course_id = int(query.data.split()[-2])
    content_id = int(query.data.split()[-1])

    module = await CourseContentDB.get_course_content_modules(content_id=content_id)

    await query.message.edit_reply_markup(
        reply_markup=modules_btns(module, course_id=course_id, content_id=content_id).as_markup()
    )


@rate_limit(limit=1)
@Logger.log_msg
@login_required
async def courses_contents_course_content_module(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    course_id = int(query.data.split()[-3])
    content_id = int(query.data.split()[-2])
    module_id = int(query.data.split()[-1])

    files = await CourseContentDB.get_course_content_module_files(module_id=module_id)
    urls = await CourseContentDB.get_course_content_module_urls(module_id=module_id)

    await query.message.edit_reply_markup(
        reply_markup=back_btn(
            data=f"courses_contents {course_id} {content_id}", kb=url_btns(urls=urls, kb=files_btns(files=files))
        ).as_markup()
    )


@rate_limit(limit=3)
@Logger.log_msg
@login_required
async def courses_send_file(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    await query.answer("Wait, file is sending...")
    await global_vars.bot.send_chat_action(query.message.chat.id, ChatAction.UPLOAD_DOCUMENT)
    file_id = int(query.data.split()[-1])

    file = await CourseContentDB.get_course_content_module_files_by_fileid(file_id=file_id)
    await query.message.answer_document(
        document=types.BufferedInputFile(file=file.bytes, filename=file.filename),
    )


def register_handlers_courses_contents(dp: Dispatcher):
    dp.callback_query.register(
        courses_send_file,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 3),
        F.func(lambda c: c.data.split()[1] == "file"),
    )

    dp.callback_query.register(courses_contents, F.func(lambda c: c.data == "courses_contents"))
    dp.callback_query.register(
        courses_contents_course,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 2),
    )
    dp.callback_query.register(
        courses_contents_course_content,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 3),
    )
    dp.callback_query.register(
        courses_contents_course_content_module,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 4),
    )
