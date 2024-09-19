from aiogram import F, Router, types
from aiogram.enums.chat_action import ChatAction

import global_vars
from modules.bot.functions.decorators import login_required
from modules.bot.keyboards.courses_contents import (
    active_courses_btns,
    back_btn,
    contents_btns,
    files_btns,
    modules_btns,
    url_btns,
)
from modules.bot.throttling import rate_limit
from modules.logger import Logger
from modules.pm_api.api import PocketMoodleAPI


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

    courses = await PocketMoodleAPI().get_courses(user_id=user_id, is_active=True)

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

    course_content = await PocketMoodleAPI().get_course_contents(course_id=course_id)

    await query.message.edit_reply_markup(
        reply_markup=(await contents_btns(course_content, course_id=course_id)).as_markup()
    )


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

    course_contents = await PocketMoodleAPI().get_course_contents(course_id)
    modules = course_contents[str(content_id)].modules

    await query.message.edit_reply_markup(
        reply_markup=(await modules_btns(modules, course_id=course_id, content_id=content_id)).as_markup()
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

    urls = await PocketMoodleAPI().get_course_content_module_urls(course_id, module_id)
    files = await PocketMoodleAPI().get_course_content_module_files(course_id, module_id)

    await query.message.edit_reply_markup(
        reply_markup=back_btn(
            data=f"courses_contents {course_id} {content_id}",
            kb=url_btns(urls=urls, kb=files_btns(files=files)),
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

    course_id = int(query.data.split()[-4])
    content_id = int(query.data.split()[-3])
    module_id = int(query.data.split()[-2])
    file_id = int(query.data.split()[-1])

    await query.answer("Wait, file is sending...")
    await global_vars.bot.send_chat_action(query.message.chat.id, ChatAction.UPLOAD_DOCUMENT)

    files = await PocketMoodleAPI().get_course_content_module_files(course_id, module_id)
    file = files[str(file_id)]

    await query.message.answer_document(
        document=types.BufferedInputFile(file=file.bytes, filename=file.filename),
    )


def register_handlers_courses_contents(router: Router):
    router.callback_query.register(courses_contents, F.func(lambda c: c.data == "courses_contents"))

    router.callback_query.register(
        courses_contents_course,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 2),
    )
    router.callback_query.register(
        courses_contents_course_content,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 3),
    )
    router.callback_query.register(
        courses_contents_course_content_module,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 4),
    )
    router.callback_query.register(
        courses_send_file,
        F.func(lambda c: c.data.split()[0] == "courses_contents"),
        F.func(lambda c: len(c.data.split()) == 3),
        F.func(lambda c: c.data.split()[1] == "file"),
    )
