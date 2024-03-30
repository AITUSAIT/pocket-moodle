from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.markdown import escape_md

from config import ENHANCED_SCHOLARSHIP_THRESHOLD, HALFTERM_MIN, RATE, RETAKE_MIN, SCHOLARSHIP_THRESHOLD, TERM_MIN
from global_vars import dp
from modules.bot.functions.deadlines import get_deadlines_local_by_course, get_deadlines_local_by_days
from modules.bot.functions.functions import add_checked_finals, check_is_valid_mail, count_active_user, delete_msg, insert_user
from modules.bot.functions.rights import login_required
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
from modules.database import CourseDB, UserDB
from modules.database.models import Course, Grade
from modules.database.notification import NotificationDB
from modules.logger import Logger
from modules.moodle import MoodleAPI, exceptions


class MoodleForm(StatesGroup):
    wait_mail = State()
    wait_api_token = State()


class Submit(StatesGroup):
    wait_file = State()
    wait_text = State()


@dp.throttled(rate=5)
async def trottle(*args, **kwargs):
    message: types.CallbackQuery | types.Message = args[0]
    rate: int | float = kwargs["rate"]

    if isinstance(message, types.Message):
        await message.answer(f"Not so fast, wait {rate} seconds\n\nSome commands cannot be called frequently")
    elif isinstance(message, types.CallbackQuery):
        await message.answer(f"Not so fast, wait {rate} seconds")


@dp.throttled(rate=RATE)
@Logger.log_msg
async def register_moodle_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        await UserDB.create_user(user_id, None)

    msg = await query.message.answer(
        f"Write your *Barcode* or *Email address* from [here]({escape_md('https://moodle.astanait.edu.kz/user/profile.php')}):",
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    await delete_msg(query.message)
    await MoodleForm.wait_mail.set()

    async with state.proxy() as data:
        data["msg_del"] = msg


@dp.throttled(rate=RATE)
@Logger.log_msg
async def register(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        await UserDB.create_user(user_id, None)

    msg = await message.answer(
        f"Write your *Barcode* or *Email address* from [here]({escape_md('https://moodle.astanait.edu.kz/user/profile.php')}):",
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    await delete_msg(message)
    await MoodleForm.wait_mail.set()

    async with state.proxy() as data:
        data["msg_del"] = msg


@dp.throttled(rate=RATE)
async def wait_mail(message: types.Message, state: FSMContext):
    if check_is_valid_mail(message.text):
        mail = message.text
    elif message.text.isnumeric():
        mail = f"{message.text}@astanait.edu.kz"
    else:
        msg = await message.answer(
            f"*Email* or *Barcode* not valid, try again❗️\n\nWrite your *Email address* from [here]({escape_md('https://moodle.astanait.edu.kz/user/profile.php')}):",
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )

        async with state.proxy() as data:
            await delete_msg(data["msg_del"], message)
            data["msg_del"] = msg
        return

    msg = await message.answer(
        f"Write your *Moodle mobile web service* Key from [here]({escape_md('https://moodle.astanait.edu.kz/user/managetoken.php')}):",
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    await MoodleForm.wait_api_token.set()

    async with state.proxy() as data:
        await delete_msg(data["msg_del"], message)
        data["msg_del"] = msg
        data["mail"] = mail


@dp.throttled(rate=RATE)
@count_active_user
async def wait_api_token(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    api_token = message.text
    async with state.proxy() as data:
        await delete_msg(data["msg_del"], message)
        mail = data["mail"]

    try:
        await MoodleAPI.check_api_token(mail, api_token)
    except exceptions.WrongToken:
        text = f"Wrong *Moodle Key*, try again❗️\n\nWrite your *Moodle mobile web service* Key from [here]({escape_md('https://moodle.astanait.edu.kz/user/managetoken.php')}):"
        state_to_set = MoodleForm.wait_api_token
    except exceptions.WrongMail:
        text = f"*Email* or *Barcode* not valid, try again❗️\n\nWrite your *Email address* from [here]({escape_md('https://moodle.astanait.edu.kz/user/profile.php')}):"
        state_to_set = MoodleForm.wait_mail
    else:
        await UserDB.register(user_id, mail, api_token)
        await NotificationDB.set_notification_status(user_id, "is_newbie_requested", True)
        await NotificationDB.set_notification_status(user_id, "error_check_token", False)
        await insert_user(user_id)

        text = "Your Moodle account is registered\!"

        await message.answer(text, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=main_menu())
        await state.finish()
        return

    msg = await message.answer(text, parse_mode=types.ParseMode.MARKDOWN_V2)
    await state_to_set.set()
    async with state.proxy() as data:
        await delete_msg(data["msg_del"], message)
        data["msg_del"] = msg
        mail = data["mail"]


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_grades(query: types.CallbackQuery):
    if not await CourseDB.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    text = "Choose option:"
    await query.message.edit_text(text, reply_markup=grades_btns())


@dp.throttled(rate=RATE)
@count_active_user
@login_required
async def get_grades_choose_course_text(query: types.CallbackQuery):
    user_id = query.from_user.id
    is_active = query.data.split()[1] == "active"
    text = "Choose one:"
    courses = await CourseDB.get_courses(user_id, is_active)
    kb = active_grades_btns(courses, is_active)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=RATE)
@count_active_user
@login_required
async def get_grades_course_text(query: types.CallbackQuery):
    user_id = query.from_user.id

    is_active = query.data.split()[1] == "active"
    course_id = int(query.data.split()[3])
    courses = await CourseDB.get_courses(user_id)
    course = courses[str(course_id)]

    text = f"[{escape_md(course.name)}]({escape_md(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course.course_id}')})\n"
    for grade in course.grades.values():
        name = grade.name
        percentage = escape_md(grade.percentage)
        if "%" in percentage:
            percentage = f"*{percentage}*"
        text += f"    {escape_md(name)}  \-  {percentage}\n"

    kb = course_back(is_active)
    await query.message.edit_text(text, reply_markup=kb, parse_mode=types.ParseMode.MARKDOWN_V2)


@dp.throttled(rate=RATE)
@count_active_user
@Logger.log_msg
@login_required
async def get_deadlines(query: types.CallbackQuery):
    if not await CourseDB.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_btns())


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_choose_courses(query: types.CallbackQuery):
    user_id = query.from_user.id

    courses = await CourseDB.get_courses(user_id, True)

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_courses_btns(courses))


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_course(query: types.CallbackQuery):
    user_id = query.from_user.id

    user = await UserDB.get_user(user_id)
    if not user:
        return

    course_id = int(query.data.split()[2])
    text = await get_deadlines_local_by_course(user, course_id)
    if not text:
        text = "So far there are no such"

    await query.message.edit_text(
        text, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=deadlines_courses_back_btns()
    )
    await query.answer()


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_choose_days(query: types.CallbackQuery):
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_days_btns())


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def get_deadlines_days(query: types.CallbackQuery):
    user_id = query.from_user.id

    user = await UserDB.get_user(user_id)
    if not user:
        return

    days = int(query.data.split()[2])
    text = await get_deadlines_local_by_days(user, days)
    if not text:
        text = "So far there are no such"

    await query.message.edit_text(text, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=deadlines_days_back_btns())
    await query.answer()


@dp.throttled(rate=RATE)
@Logger.log_msg
@count_active_user
@login_required
async def submit_assign_show_courses(query: types.CallbackQuery | types.Message):
    text = "Choose one:"
    if isinstance(query, types.CallbackQuery):
        user_id = query.from_user.id

        courses = await CourseDB.get_courses(user_id, is_active=True)

        await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    elif isinstance(query, types.Message):
        message = query
        user_id = message.from_user.id

        courses = await CourseDB.get_courses(user_id, is_active=True)

        await message.answer(text, reply_markup=show_courses_for_submit(courses))


@dp.throttled(rate=RATE)
@login_required
async def submit_assign_cancel(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    courses = await CourseDB.get_courses(user_id, True)

    text = "Choose one:"
    await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    await state.finish()


@dp.throttled(rate=RATE)
@login_required
async def submit_assign_show_assigns(query: types.CallbackQuery):
    user_id = query.from_user.id
    course_id = query.data.split()[1]

    courses: dict[str, Course] = await CourseDB.get_courses(user_id, True)

    assigns = courses[course_id].deadlines

    await query.message.edit_reply_markup(reply_markup=show_assigns_for_submit(assigns, course_id))


@dp.throttled(rate=RATE)
@login_required
async def submit_assign_choose_type(query: types.CallbackQuery):
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]

    await query.message.edit_reply_markup(reply_markup=show_assigns_type(course_id, assign_id))


@dp.throttled(rate=RATE)
@login_required
async def submit_assign_wait(query: types.CallbackQuery, state: FSMContext):
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]
    submit_type = query.data.split()[3]

    if submit_type == "file":
        text = "Send file as document for submit (support only one)"
        await Submit.wait_file.set()
    elif submit_type == "text":
        text = "Send text for submit"
        await Submit.wait_text.set()

    msg = await query.message.edit_text(text, reply_markup=show_assigns_cancel_btn())

    async with state.proxy() as data:
        data["course_id"] = course_id
        data["assign_id"] = assign_id
        data["type"] = submit_type
        data["msg"] = msg


@dp.throttled(rate=RATE)
@count_active_user
@login_required
async def submit_assign_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        return

    async with state.proxy() as data:
        course_id = data["course_id"]
        assign_id = data["assign_id"]

    courses = await CourseDB.get_courses(user_id, True)
    course = courses[str(course_id)]
    assign = course.deadlines[assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course.course_id}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign.id}"

    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    file_name = file_path.split("/")[-1]

    my_object = None
    file_to_upload = await message.bot.download_file(file_path, my_object)

    data_file = await MoodleAPI.upload_file(file_to_upload, file_name, user.api_token)
    item_id = data_file[0]["itemid"]
    result = await MoodleAPI.save_submission(token=user.api_token, assign_id=assign.assign_id, item_id=item_id)
    if result == []:
        await message.answer(
            f"[{escape_md(course.name)}]({escape_md(url_to_course)})\n[{escape_md(assign.name)}]({escape_md(url_to_assign)})\n\nFile submitted\!",
            reply_markup=add_delete_button(),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        if isinstance(result, list):
            await message.answer(
                f"Error: {result[0].get('item', None)}\n{result[0].get('message', None)}",
                reply_markup=add_delete_button(),
            )
        else:
            await message.answer(
                f"Error: {result.get('item', None)}\n{result.get('message', None)}", reply_markup=add_delete_button()
            )

    async with state.proxy() as data:
        await delete_msg(data["msg"], message)
    await state.finish()


@dp.throttled(rate=RATE)
@count_active_user
@login_required
async def submit_assign_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        return

    async with state.proxy() as data:
        course_id = data["course_id"]
        assign_id = data["assign_id"]

    courses = await CourseDB.get_courses(user_id, True)
    course = courses[str(course_id)]
    assign = course.deadlines[assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course.course_id}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign.id}"

    result = await MoodleAPI.save_submission(user.api_token, assign.assign_id, text=message.text)
    if result == []:
        await message.answer(
            f"[{escape_md(course.name)}]({escape_md(url_to_course)})\n[{escape_md(assign.name)}]({escape_md(url_to_assign)})\n\Text submitted\!",
            reply_markup=add_delete_button(),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await message.answer(f"Error: {result[0]['message']}", reply_markup=add_delete_button())

    async with state.proxy() as data:
        await delete_msg(data["msg"], message)
    await state.finish()


@dp.throttled(trottle, rate=15)
@count_active_user
@Logger.log_msg
@login_required
async def update(message: types.Message):
    user_id = message.from_user.id

    await insert_user(user_id)
    await message.reply("Wait, you're first in queue for an update", reply_markup=add_delete_button())
    await NotificationDB.set_notification_status(user_id, "is_update_requested", True)


@dp.throttled(trottle, rate=15)
@count_active_user
@Logger.log_msg
@login_required
async def check_finals(message: types.Message):
    user_id = message.from_user.id
    if not await CourseDB.is_ready_courses(user_id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await message.answer(text, reply_markup=main_menu())
        return

    courses = await CourseDB.get_courses(user_id, True)
    try:
        text = ""
        active_courses = [course for course in courses.values() if course.active]
        text += f"\n*🔴 To save the scholarship \(\>{SCHOLARSHIP_THRESHOLD}\)*:\n"

        text = add_checked_finals(text, active_courses, 'scholarship')

        text += f"\n*🔵 To receive an enhanced scholarship \(\>{ENHANCED_SCHOLARSHIP_THRESHOLD}\)*:\n"

        text = add_checked_finals(text, active_courses, 'enhanced scholarship')

        text += f"\n*⚪️ If you pass the Final 100%, you will get a Total:*\n"

        text = add_checked_finals(text, active_courses, 'max possible')

        await message.answer(text, parse_mode="MarkdownV2")
    except Exception as exc:
        Logger.error(exc, exc_info=True)


def register_handlers_moodle(dp: Dispatcher):
    dp.register_message_handler(register, commands="register", state="*")
    dp.register_message_handler(wait_mail, content_types=["text"], state=MoodleForm.wait_mail)
    dp.register_message_handler(wait_api_token, content_types=["text"], state=MoodleForm.wait_api_token)

    dp.register_message_handler(submit_assign_show_courses, commands="submit_assignment", state="*")

    dp.register_message_handler(update, commands="update", state="*")

    dp.register_message_handler(check_finals, commands="check_finals", state="*")

    dp.register_message_handler(submit_assign_text, content_types=["text"], state=Submit.wait_text)
    dp.register_message_handler(submit_assign_file, content_types=["document"], state=Submit.wait_file)

    dp.register_callback_query_handler(register_moodle_query, lambda c: c.data == "register", state="*")

    dp.register_callback_query_handler(get_grades, lambda c: c.data == "get_grades", state="*")
    dp.register_callback_query_handler(
        get_grades_choose_course_text,
        lambda c: c.data.split()[0] == "get_grades",
        lambda c: c.data.split()[2] == "text",
        lambda c: len(c.data.split()) == 3,
        state="*",
    )
    dp.register_callback_query_handler(
        get_grades_course_text,
        lambda c: c.data.split()[0] == "get_grades",
        lambda c: c.data.split()[2] == "text",
        lambda c: len(c.data.split()) == 4,
        state="*",
    )

    dp.register_callback_query_handler(get_deadlines, lambda c: c.data == "get_deadlines", state="*")

    dp.register_callback_query_handler(
        get_deadlines_choose_courses, lambda c: c.data == "get_deadlines active", state="*"
    )
    dp.register_callback_query_handler(
        get_deadlines_course,
        lambda c: c.data.split()[0] == "get_deadlines",
        lambda c: c.data.split()[1] == "active",
        state="*",
    )

    dp.register_callback_query_handler(get_deadlines_choose_days, lambda c: c.data == "get_deadlines days", state="*")
    dp.register_callback_query_handler(
        get_deadlines_days,
        lambda c: c.data.split()[0] == "get_deadlines",
        lambda c: c.data.split()[1] == "days",
        state="*",
    )

    dp.register_callback_query_handler(submit_assign_show_courses, lambda c: c.data == "submit_assign", state="*")
    dp.register_callback_query_handler(
        submit_assign_cancel,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: c.data.split()[1] == "cancel",
        lambda c: len(c.data.split()) == 2,
        state="*",
    )
    dp.register_callback_query_handler(
        submit_assign_show_assigns,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 2,
        state="*",
    )
    dp.register_callback_query_handler(
        submit_assign_choose_type,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 3,
        state="*",
    )
    dp.register_callback_query_handler(
        submit_assign_wait,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 4,
        state="*",
    )
