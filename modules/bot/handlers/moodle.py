import aiohttp
import aiohttp.http_exceptions
from aiogram import F, Router, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types.message import Message

import global_vars
from config import ENHANCED_SCHOLARSHIP_THRESHOLD, RATE, SCHOLARSHIP_THRESHOLD
from modules.bot.functions.deadlines import get_deadlines_local_by_course, get_deadlines_local_by_days
from modules.bot.functions.decorators import login_required
from modules.bot.functions.functions import (
    add_checked_finals,
    check_is_valid_mail,
    count_active_user,
    delete_msg,
    escape_md,
)
from modules.bot.keyboards.default import add_delete_button, main_menu
from modules.bot.keyboards.moodle import (
    active_grades_btns,
    course_back,
    deadlines_btns,
    deadlines_courses_back_btns,
    deadlines_courses_btns,
    deadlines_days_back_btns,
    deadlines_days_btns,
    grades_btns,
    show_assigns_cancel_btn,
    show_assigns_for_submit,
    show_assigns_type,
    show_courses_for_submit,
)
from modules.bot.throttling import rate_limit
from modules.logger import Logger
from modules.moodle import MoodleAPI, exceptions
from modules.pm_api.api import PocketMoodleAPI
from modules.pm_api.models import Course


class MoodleForm(StatesGroup):
    wait_api_token = State()


class Submit(StatesGroup):
    wait_file = State()
    wait_text = State()


@rate_limit(limit=RATE)
@Logger.log_msg
async def register_moodle_query(query: types.CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.answer()

    user_id = query.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        await PocketMoodleAPI().create_user(user_id)

    msg = await query.message.answer(
        f"Write your *Barcode* or *Email address* from [here]({escape_md('https://moodle.astanait.edu.kz/user/profile.php')}):",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await delete_msg(query.message)
    await state.set_state(MoodleForm.wait_api_token)
    await state.set_data({"msg_del": msg})


@rate_limit(limit=RATE)
@Logger.log_msg
async def register(message: types.Message, state: FSMContext):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        await PocketMoodleAPI().create_user(user_id)

    msg = await message.answer(
        f"Write your *Moodle mobile web service* Key from [here]({escape_md('https://moodle.astanait.edu.kz/user/managetoken.php')}):",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await delete_msg(message)
    await state.set_state(MoodleForm.wait_api_token)
    await state.set_data({"msg_del": msg})


@rate_limit(limit=RATE)
@count_active_user
async def wait_api_token(message: types.Message, state: FSMContext):
    if message.from_user is None:
        return
    if message.text is None:
        return
    user_id = message.from_user.id
    api_token = message.text
    data = await state.get_data()
    await delete_msg(data["msg_del"], message)

    try:
        result = await MoodleAPI.check_api_token(api_token)
    except exceptions.WrongToken:
        text = f"Wrong *Moodle Key*, try again❗️\n\nWrite your *Moodle mobile web service* Key from [here]({escape_md('https://moodle.astanait.edu.kz/user/managetoken.php')}):"
        state_to_set = MoodleForm.wait_api_token
    except aiohttp.ClientError:
        text = f"Try again❗️\n\nCannot check your *Moodle Key*, maybe Moodle website is down"
        state_to_set = MoodleForm.wait_api_token
    except aiohttp.ClientResponseError:
        text = f"Try again❗️\n\nCannot check your *Moodle Key*, maybe Moodle website is down"
        state_to_set = MoodleForm.wait_api_token
    else:

        await PocketMoodleAPI().register_moodle(user_id, result["username"], api_token, moodle_id=result["userid"])
        notification_status = await PocketMoodleAPI().get_notification_status(user_id)
        notification_status.is_newbie_requested = True
        notification_status.is_update_requested = False
        await PocketMoodleAPI().set_notification_status(user_id, notification_status)
        await PocketMoodleAPI().insert_user(user_id)

        text = "Your Moodle account is registered\!"

        await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=main_menu().as_markup())
        await state.clear()
        return

    msg = await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(state_to_set)
    data = await state.get_data()
    await delete_msg(data["msg_del"], message)
    data["msg_del"] = msg
    await state.set_data(data)


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_grades(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if not await PocketMoodleAPI().is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu().as_markup())
        return

    text = "Choose option:"
    await query.message.edit_text(text, reply_markup=grades_btns().as_markup())


@rate_limit(limit=RATE)
@count_active_user
@login_required
async def get_grades_choose_course_text(query: types.CallbackQuery):
    if query.data is None:
        return
    if not isinstance(query.message, Message):
        return
    user_id = query.from_user.id
    is_active = query.data.split()[1] == "active"
    text = "Choose one:"
    courses = await PocketMoodleAPI().get_courses(user_id, is_active)
    kb = active_grades_btns(courses, is_active)
    await query.message.edit_text(text, reply_markup=kb.as_markup())


@rate_limit(limit=RATE)
@count_active_user
@login_required
async def get_grades_course_text(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    user_id = query.from_user.id

    is_active = query.data.split()[1] == "active"
    course_id = int(query.data.split()[3])
    course = await PocketMoodleAPI().get_course(user_id, course_id)
    grades = await PocketMoodleAPI().get_grades(user_id, course_id)
    grades = dict(sorted(grades.items(), key=lambda item: item[1].grade_id))

    text = f"[{escape_md(course.name)}]({escape_md(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course.course_id}')})\n_{escape_md(course.teacher_name)}_\n"
    for grade in grades.values():
        name = grade.name
        percentage = escape_md(grade.percentage)
        if "%" in percentage:
            percentage = f"*{percentage}*"
        text += f"    {escape_md(name)}  \-  {percentage}\n"

    kb = course_back(is_active)
    await query.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.MARKDOWN_V2)


@rate_limit(limit=RATE)
@count_active_user
@Logger.log_msg
@login_required
async def get_deadlines(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if not await PocketMoodleAPI().is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu().as_markup())
        return

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_btns().as_markup())


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_choose_courses(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    user_id = query.from_user.id

    courses = await PocketMoodleAPI().get_courses(user_id, True)

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_courses_btns(courses).as_markup())


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_course(query: types.CallbackQuery):
    if query.data is None:
        return
    if not isinstance(query.message, Message):
        return
    user_id = query.from_user.id

    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        return

    course_id = int(query.data.split()[2])
    text = await get_deadlines_local_by_course(user, course_id)
    if not text:
        text = "So far there are no such"

    await query.message.edit_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=deadlines_courses_back_btns().as_markup()
    )
    await query.answer()


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_choose_days(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_days_btns().as_markup())


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_days(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    user_id = query.from_user.id

    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        return

    days = int(query.data.split()[2])
    text = await get_deadlines_local_by_days(user, days)
    if not text:
        text = "So far there are no such"

    await query.message.edit_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=deadlines_days_back_btns().as_markup()
    )
    await query.answer()


@rate_limit(limit=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def submit_assign_show_courses(query: types.CallbackQuery | types.Message):
    text = "Choose one:"
    if isinstance(query, types.CallbackQuery):
        if not isinstance(query.message, Message):
            return
        user_id = query.from_user.id

        courses = await PocketMoodleAPI().get_courses(user_id, is_active=True)

        await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses).as_markup())
    elif isinstance(query, types.Message):
        if query.from_user is None:
            return
        user_id = query.from_user.id

        courses = await PocketMoodleAPI().get_courses(user_id, is_active=True)

        await query.answer(text, reply_markup=show_courses_for_submit(courses).as_markup())


@rate_limit(limit=RATE)
@login_required
async def submit_assign_cancel(query: types.CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    user_id = query.from_user.id

    courses = await PocketMoodleAPI().get_courses(user_id, True)

    text = "Choose one:"
    await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses).as_markup())
    await state.clear()


@rate_limit(limit=RATE)
@login_required
async def submit_assign_show_assigns(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    user_id = query.from_user.id
    course_id = int(query.data.split()[1])

    deadlines = await PocketMoodleAPI().get_deadlines(user_id, course_id)

    await query.message.edit_reply_markup(reply_markup=show_assigns_for_submit(deadlines, str(course_id)).as_markup())


@rate_limit(limit=RATE)
@login_required
async def submit_assign_choose_type(query: types.CallbackQuery):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]

    await query.message.edit_reply_markup(reply_markup=show_assigns_type(course_id, assign_id).as_markup())


@rate_limit(limit=RATE)
@login_required
async def submit_assign_wait(query: types.CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    if query.data is None:
        return
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]
    submit_type = query.data.split()[3]

    text = ""
    if submit_type == "file":
        text = "Send file as document for submit (support only one)"
        await state.set_state(Submit.wait_file)
    elif submit_type == "text":
        text = "Send text for submit"
        await state.set_state(Submit.wait_text)

    msg = await query.message.edit_text(text, reply_markup=show_assigns_cancel_btn().as_markup())

    data = await state.get_data()
    data["course_id"] = course_id
    data["assign_id"] = assign_id
    data["type"] = submit_type
    data["msg"] = msg
    await state.set_data(data)


@rate_limit(limit=RATE)
@count_active_user
@login_required
async def submit_assign_file(message: types.Message, state: FSMContext):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        return
    if not user.api_token:
        return

    data = await state.get_data()
    course_id = data["course_id"]
    assign_id = data["assign_id"]
    await state.set_data(data)

    course = await PocketMoodleAPI().get_course(user_id, course_id)
    deadlines = await PocketMoodleAPI().get_deadlines(user_id, course_id)
    assign = deadlines[str(assign_id)]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course.course_id}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign.id}"

    if message.document is None:
        return
    file_id = message.document.file_id
    file = await global_vars.bot.get_file(file_id)
    file_path = file.file_path
    if file_path is None:
        return
    file_name = file_path.split("/")[-1]

    my_object = None
    file_to_upload = await global_vars.bot.download_file(file_path, my_object)

    if file_to_upload is None:
        return
    data_file = await MoodleAPI.upload_file(file_to_upload, file_name, user.api_token)
    item_id = data_file[0]["itemid"]
    result = await MoodleAPI.save_submission(token=user.api_token, assign_id=assign.assign_id, item_id=item_id)
    if result == []:
        await message.answer(
            f"[{escape_md(course.name)}]({escape_md(url_to_course)})\n[{escape_md(assign.name)}]({escape_md(url_to_assign)})\n\nFile submitted\!",
            reply_markup=add_delete_button().as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        if isinstance(result, list):
            await message.answer(
                f"Error: {result[0].get('item', None)}\n{result[0].get('message', None)}",
                reply_markup=add_delete_button().as_markup(),
            )
        else:
            await message.answer(
                f"Error: {result.get('item', None)}\n{result.get('message', None)}",
                reply_markup=add_delete_button().as_markup(),
            )

    data = await state.get_data()
    await delete_msg(data["msg"], message)
    await state.clear()


@rate_limit(limit=RATE)
@count_active_user
@login_required
async def submit_assign_text(message: types.Message, state: FSMContext):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        return
    if not user.api_token:
        return

    data = await state.get_data()
    course_id = data["course_id"]
    assign_id = data["assign_id"]

    course = await PocketMoodleAPI().get_course(user_id, course_id)
    deadlines = await PocketMoodleAPI().get_deadlines(user_id, course_id)
    assign = deadlines[assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course.course_id}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign.id}"

    result = await MoodleAPI.save_submission(user.api_token, assign.assign_id, text=message.text)
    if result == []:
        await message.answer(
            f"[{escape_md(course.name)}]({escape_md(url_to_course)})\n[{escape_md(assign.name)}]({escape_md(url_to_assign)})\n\Text submitted\!",
            reply_markup=add_delete_button().as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        await message.answer(f"Error: {result[0]['message']}", reply_markup=add_delete_button().as_markup())

    data = await state.get_data()
    await delete_msg(data["msg"], message)
    await state.clear()


@rate_limit(limit=RATE)
@count_active_user
@Logger.log_msg
@login_required
async def update(message: types.Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id

    await PocketMoodleAPI().insert_user(user_id)
    await message.reply("Wait, you're first in queue for an update", reply_markup=add_delete_button().as_markup())
    notification_status = await PocketMoodleAPI().get_notification_status(user_id)
    notification_status.is_update_requested = True
    await PocketMoodleAPI().set_notification_status(user_id, notification_status)


@rate_limit(limit=RATE)
@count_active_user
@Logger.log_msg
@login_required
async def check_finals(message: types.Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    if not await PocketMoodleAPI().is_ready_courses(user_id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await message.answer(text, reply_markup=main_menu().as_markup())
        return

    courses = await PocketMoodleAPI().get_courses(user_id, True)
    try:
        text = ""
        active_courses = [course for course in courses.values() if course.active]
        text += f"\n\n*🔴 To save the scholarship \(\>{SCHOLARSHIP_THRESHOLD}\)*:\n"

        text = await add_checked_finals(user_id, text, active_courses, "scholarship")

        text += f"\n\n*🔵 To receive an enhanced scholarship \(\>{ENHANCED_SCHOLARSHIP_THRESHOLD}\)*:\n"

        text = await add_checked_finals(user_id, text, active_courses, "enhanced scholarship")

        text += "\n\n*⚪️ If you pass the Final 100%, you will get a Total:*\n"

        text = await add_checked_finals(user_id, text, active_courses, "max possible")

        await message.answer(text, parse_mode="MarkdownV2")
    except Exception as exc:
        Logger.error(exc, exc_info=True)


def register_handlers_moodle(router: Router):
    router.message.register(register, Command("register"))
    router.message.register(wait_api_token, F.text, MoodleForm.wait_api_token)

    router.message.register(submit_assign_show_courses, Command("submit_assignment"))

    router.message.register(update, Command("update"))

    router.message.register(check_finals, Command("check_finals"))

    router.message.register(submit_assign_text, F.text, Submit.wait_text)
    router.message.register(submit_assign_file, F.document, Submit.wait_file)

    router.callback_query.register(register_moodle_query, F.func(lambda c: c.data == "register"))

    router.callback_query.register(get_grades, F.func(lambda c: c.data == "get_grades"))
    router.callback_query.register(
        get_grades_choose_course_text,
        F.func(lambda c: c.data.split()[0] == "get_grades"),
        F.func(lambda c: c.data.split()[2] == "text"),
        F.func(lambda c: len(c.data.split()) == 3),
    )
    router.callback_query.register(
        get_grades_course_text,
        F.func(lambda c: c.data.split()[0] == "get_grades"),
        F.func(lambda c: c.data.split()[2] == "text"),
        F.func(lambda c: len(c.data.split()) == 4),
    )

    router.callback_query.register(get_deadlines, F.func(lambda c: c.data == "get_deadlines"))

    router.callback_query.register(get_deadlines_choose_courses, F.func(lambda c: c.data == "get_deadlines active"))
    router.callback_query.register(
        get_deadlines_course,
        F.func(lambda c: c.data.split()[0] == "get_deadlines"),
        F.func(lambda c: c.data.split()[1] == "active"),
    )

    router.callback_query.register(get_deadlines_choose_days, F.func(lambda c: c.data == "get_deadlines days"))
    router.callback_query.register(
        get_deadlines_days,
        F.func(lambda c: c.data.split()[0] == "get_deadlines"),
        F.func(lambda c: c.data.split()[1] == "days"),
    )

    router.callback_query.register(submit_assign_show_courses, F.func(lambda c: c.data == "submit_assign"))
    router.callback_query.register(
        submit_assign_cancel,
        F.func(lambda c: c.data.split()[0] == "submit_assign"),
        F.func(lambda c: c.data.split()[1] == "cancel"),
        F.func(lambda c: len(c.data.split()) == 2),
    )
    router.callback_query.register(
        submit_assign_show_assigns,
        F.func(lambda c: c.data.split()[0] == "submit_assign"),
        F.func(lambda c: len(c.data.split()) == 2),
    )
    router.callback_query.register(
        submit_assign_choose_type,
        F.func(lambda c: c.data.split()[0] == "submit_assign"),
        F.func(lambda c: len(c.data.split()) == 3),
    )
    router.callback_query.register(
        submit_assign_wait,
        F.func(lambda c: c.data.split()[0] == "submit_assign"),
        F.func(lambda c: len(c.data.split()) == 4),
    )
