from io import BytesIO

from aiogram import Dispatcher, types

from global_vars import dp
from modules.bot.functions.rights import login_required
from modules.bot.handlers.moodle import trottle
from modules.bot.keyboards.courses_contents import (
    active_courses_btns,
    back_btn,
    contents_btns,
    files_btns,
    modules_btns,
    url_btns,
)
from modules.database import CourseContentDB, CourseDB
from modules.logger import Logger


@dp.throttled(rate=1)
@Logger.log_msg
@login_required
async def courses_contents(query: types.CallbackQuery):
    user_id = query.from_user.id

    courses = await CourseDB.get_courses(user_id=user_id, is_active=True)

    await query.message.edit_text("Choose:", reply_markup=active_courses_btns(courses=courses))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
@login_required
async def courses_contents_course(query: types.CallbackQuery):
    course_id = int(query.data.split()[-1])

    course_content = await CourseContentDB.get_course_contents(course_id=course_id)

    await query.message.edit_reply_markup(reply_markup=contents_btns(course_content, course_id=course_id))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
@login_required
async def courses_contents_course_content(query: types.CallbackQuery):
    course_id = int(query.data.split()[-2])
    content_id = int(query.data.split()[-1])

    module = await CourseContentDB.get_course_content_modules(content_id=content_id)

    await query.message.edit_reply_markup(reply_markup=modules_btns(module, course_id=course_id, content_id=content_id))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
@login_required
async def courses_contents_course_content_module(query: types.CallbackQuery):
    course_id = int(query.data.split()[-3])
    content_id = int(query.data.split()[-2])
    module_id = int(query.data.split()[-1])

    files = await CourseContentDB.get_course_content_module_files(module_id=module_id)
    urls = await CourseContentDB.get_course_content_module_urls(module_id=module_id)

    await query.message.edit_reply_markup(
        reply_markup=back_btn(
            data=f"courses_contents {course_id} {content_id}", kb=url_btns(urls=urls, kb=files_btns(files=files))
        )
    )


@dp.throttled(trottle, rate=3)
@Logger.log_msg
@login_required
async def courses_send_file(query: types.CallbackQuery):
    await query.answer("Wait, file is sending...")
    await query.bot.send_chat_action(query.message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)
    file_id = int(query.data.split()[-1])

    file = await CourseContentDB.get_course_content_module_files_by_fileid(file_id=file_id)
    await query.message.answer_document(
        document=types.InputFile(BytesIO(file.bytes), filename=file.filename),
    )


def register_handlers_courses_contents(dp: Dispatcher):
    dp.register_callback_query_handler(
        courses_send_file,
        lambda c: c.data.split()[0] == "courses_contents",
        lambda c: len(c.data.split()) == 3,
        lambda c: c.data.split()[1] == "file",
        state="*",
    )

    dp.register_callback_query_handler(courses_contents, lambda c: c.data == "courses_contents", state="*")
    dp.register_callback_query_handler(
        courses_contents_course,
        lambda c: c.data.split()[0] == "courses_contents",
        lambda c: len(c.data.split()) == 2,
        state="*",
    )
    dp.register_callback_query_handler(
        courses_contents_course_content,
        lambda c: c.data.split()[0] == "courses_contents",
        lambda c: len(c.data.split()) == 3,
        state="*",
    )
    dp.register_callback_query_handler(
        courses_contents_course_content_module,
        lambda c: c.data.split()[0] == "courses_contents",
        lambda c: len(c.data.split()) == 4,
        state="*",
    )
