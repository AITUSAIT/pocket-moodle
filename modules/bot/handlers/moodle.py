from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import dp, rate
from modules.database.notification import NotificationDB
from modules.moodle import exceptions

from ...database import CourseDB, UserDB
from ...database.models import Course, Grade, User
from ...logger import Logger
from ...moodle import MoodleAPI
from ..functions.deadlines import (get_deadlines_local_by_course,
                                   get_deadlines_local_by_days)
from ..functions.functions import (check_is_valid_mail, clear_MD,
                                   count_active_user, delete_msg)
from ..functions.rights import login_and_active_sub_required, login_required
from ..keyboards.default import add_delete_button, main_menu
from ..keyboards.moodle import (active_grades_btns, course_back,
                                deadlines_btns, deadlines_courses_back_btns, deadlines_courses_btns, deadlines_days_back_btns,
                                deadlines_days_btns, grades_btns,
                                register_moodle_query, show_assigns_cancel_btn,
                                show_assigns_for_submit, show_assigns_type,
                                show_courses_for_submit)


class MoodleForm(StatesGroup):
    wait_mail = State()
    wait_api_token = State()


class Submit(StatesGroup):
    wait_file = State()
    wait_text = State()


@dp.throttled(rate=5)
async def trottle(*args, **kwargs):
    message = args[0]
    rate = kwargs['rate']

    if message.__class__ is types.Message:
        await message.answer(f"Not so fast, wait {rate} seconds\n\nSome commands cannot be called frequently")
    elif message.__class__ is types.CallbackQuery:
        await message.answer(f"Not so fast, wait {rate} seconds")
    

@dp.throttled(rate=rate)
@Logger.log_msg
async def register_moodle_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)
    
    if not user:
        await UserDB.create_user(user_id, None)
    
    msg = await query.message.answer(f"Write your *Barcode* or *Email address* from [here]({clear_MD('https://moodle.astanait.edu.kz/user/profile.php')}):", parse_mode='MarkdownV2')
    await delete_msg(query.message)
    await MoodleForm.wait_mail.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


@dp.throttled(rate=rate)
@Logger.log_msg
async def register(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user: User = await UserDB.get_user(user_id)

    if not user:
        await UserDB.new_user(user_id)
    
    msg = await message.answer(f"Write your *Barcode* or *Email address* from [here]({clear_MD('https://moodle.astanait.edu.kz/user/profile.php')}):", parse_mode='MarkdownV2')
    await delete_msg(message)
    await MoodleForm.wait_mail.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


@dp.throttled(rate=rate)
async def wait_mail(message: types.Message, state: FSMContext):
    if check_is_valid_mail(message.text):
        mail = message.text
    elif message.text.isnumeric():
        mail = f"{message.text}@astanait.edu.kz"
    else:
        msg = await message.answer(f"*Email* or *Barcode* not valid, try again❗️\n\nWrite your *Email address* from [here]({clear_MD('https://moodle.astanait.edu.kz/user/profile.php')}):", parse_mode='MarkdownV2')

        async with state.proxy() as data:
            await delete_msg(data['msg_del'], message)
            data['msg_del'] = msg
        return

    msg = await message.answer(f"Write your *Moodle mobile web service* Key from [here]({clear_MD('https://moodle.astanait.edu.kz/user/managetoken.php')}):", parse_mode='MarkdownV2')
    await MoodleForm.wait_api_token.set()

    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)
        data['msg_del'] = msg
        data['mail'] = mail


@dp.throttled(rate=rate)
@count_active_user
async def wait_api_token(message: types.Message, state: FSMContext):
    from ...app.api.router import insert_user
    user_id = message.from_user.id
    user: User = await UserDB.get_user(user_id)
    api_token = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)
        mail = data['mail']

    try:
        await MoodleAPI.check_api_token(mail, api_token)
    except exceptions.WrongToken:
        text = f"Wrong *Moodle Key*, try again❗️\n\nWrite your *Moodle mobile web service* Key from [here]({clear_MD('https://moodle.astanait.edu.kz/user/managetoken.php')}):"
        state_to_set = MoodleForm.wait_api_token
    except exceptions.WrongMail:
        text = f"*Email* or *Barcode* not valid, try again❗️\n\nWrite your *Email address* from [here]({clear_MD('https://moodle.astanait.edu.kz/user/profile.php')}):"
        state_to_set = MoodleForm.wait_mail
    else:
        await UserDB.register(user_id, mail, api_token)
        await insert_user(user_id)

        text = "Your Moodle account is registered\!"
        if not user.is_active_sub():
            text += "\n\nAvailable functions:\n" \
                    "\- Grades \(without notifications\)\n" \
                    "\- Deadlines \(without notifications\)\n\n" \
                    "To get access to all the features you need to purchase a subscription"
        
        await message.answer(text, parse_mode='MarkdownV2', reply_markup=main_menu())
        await state.finish()
        return
    
    msg = await message.answer(text, parse_mode='MarkdownV2')
    await state_to_set.set()
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)
        data['msg_del'] = msg
        mail = data['mail']    


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_grades(query: types.CallbackQuery, state: FSMContext):
    if not await CourseDB.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    text = "Choose option:"
    await query.message.edit_text(text, reply_markup=grades_btns())


@dp.throttled(rate=rate)
@login_required
async def get_grades_choose_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    is_active = True if query.data.split()[1] == 'active' else False
    text = "Choose one:"
    courses: list[Course] = await CourseDB.get_courses(user_id, is_active)
    kb = active_grades_btns(courses, is_active)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
@count_active_user
@login_required
async def get_grades_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    is_active = True if query.data.split()[1] == 'active' else False
    course_id = int(query.data.split()[3])
    course = await CourseDB.get_course(user_id, course_id)

    text = f"[{clear_MD(course.name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course.course_id}')})\n"
    for grade in course.grades.values():
        name = grade.name
        percentage = clear_MD(grade.percentage)
        if '%' in percentage:
            percentage = f"*{percentage}*"
        text += f"    {clear_MD(name)}  \-  {percentage}\n"

    kb = course_back(is_active)
    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@count_active_user
@Logger.log_msg
@login_required
async def get_deadlines(query: types.CallbackQuery, state: FSMContext):
    if not await CourseDB.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return
    
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_btns())


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_deadlines_choose_courses(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    courses: list[Course] = await CourseDB.get_courses(user_id, True)
    
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_courses_btns(courses))


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_deadlines_course(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    user: User = await UserDB.get_user(user_id)
    
    id = int(query.data.split()[2])
    text = await get_deadlines_local_by_course(user, id)
    if not text:
        text = 'So far there are no such' 
    
    await query.message.edit_text(text, parse_mode='Markdown', reply_markup=deadlines_courses_back_btns())
    await query.answer()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_deadlines_choose_days(query: types.CallbackQuery, state: FSMContext):
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_days_btns())


@dp.throttled(rate=rate)
@count_active_user
@Logger.log_msg
@login_required
async def get_deadlines_days(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    user: User = await UserDB.get_user(user_id)

    days = int(query.data.split()[2])
    text = await get_deadlines_local_by_days(user, days)
    if not text:
        text = 'So far there are no such' 

    await query.message.edit_text(text, parse_mode='Markdown', reply_markup=deadlines_days_back_btns())
    await query.answer()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def submit_assign_show_courses(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        user_id = query.from_user.id

        courses: dict[str, Course] = await CourseDB.get_courses(user_id, True)

        text = f"Choose one:"
        await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    elif query.__class__ is types.Message:
        message : types.Message = query
        user_id = message.from_user.id

        courses: dict[str, Course] = await CourseDB.get_courses(user_id, True)

        await message.answer("Choose one:", reply_markup=show_courses_for_submit(courses))


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_cancel(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    courses: list[Course] = await CourseDB.get_courses(user_id, True)

    text = f"Choose one:"
    await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    await state.finish()


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_show_assigns(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    course_id = query.data.split()[1]
    
    courses: dict[str, Course] = await CourseDB.get_courses(user_id, True)

    assigns = courses[course_id].deadlines

    await query.message.edit_reply_markup(reply_markup=show_assigns_for_submit(assigns, course_id))


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_choose_type(query: types.CallbackQuery, state: FSMContext):
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]
    
    await query.message.edit_reply_markup(reply_markup=show_assigns_type(course_id, assign_id))


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_wait(query: types.CallbackQuery, state: FSMContext):
    course_id = query.data.split()[1]
    assign_id = query.data.split()[2]
    type = query.data.split()[3]
    
    if type == "file":
        text = "Send file as document for submit (support only one)"
        await Submit.wait_file.set()
    elif type == "text":
        text = "Send text for submit"
        await Submit.wait_text.set()

    msg = await query.message.edit_text(text, reply_markup=show_assigns_cancel_btn())

    async with state.proxy() as data:
        data['course_id'] = course_id
        data['assign_id'] = assign_id
        data['type'] = type
        data['msg'] = msg


@dp.throttled(rate=rate)
@count_active_user
@login_and_active_sub_required
async def submit_assign_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user: User = await UserDB.get_user(user_id)
    async with state.proxy() as data:
        course_id = data['course_id']
        assign_id = data['assign_id']

    course = await CourseDB.get_course(user_id, course_id)
    assign = course['assignments'][assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course['id']}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign['id']}"
    
    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    file_name = file_path.split('/')[-1]

    my_object = None
    file_to_upload = await message.bot.download_file(file_path, my_object)

    data_file = await MoodleAPI.upload_file(file_to_upload, file_name, user.api_token)
    item_id = data_file[0]['itemid']
    result = await MoodleAPI.save_submission(user.api_token, assign['assign_id'], item_id=item_id)
    if result == []:
        await message.answer(f"[{clear_MD(course['name'])}]({clear_MD(url_to_course)})\n[{clear_MD(assign['name'])}]({clear_MD(url_to_assign)})\n\nFile submitted\!", reply_markup=add_delete_button(), parse_mode='MarkdownV2')
    else:
        if type(result) is list:
            await message.answer(f"Error: {result[0].get('item', None)}\n{result[0].get('message', None)}", reply_markup=add_delete_button())
        else:
            await message.answer(f"Error: {result.get('item', None)}\n{result.get('message', None)}", reply_markup=add_delete_button())

    async with state.proxy() as data:
        await delete_msg(data['msg'], message)
    await state.finish()


@dp.throttled(rate=rate)
@count_active_user
@login_and_active_sub_required
async def submit_assign_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user: User = await UserDB.get_user(user_id)
    async with state.proxy() as data:
        course_id = data['course_id']
        assign_id = data['assign_id']

    course = await CourseDB.get_course(user_id, course_id)
    assign = course['assignments'][assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course['id']}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign['id']}"

    
    result = await MoodleAPI.save_submission(user.api_token, assign['assign_id'], text=message.text)
    if result == []:
        await message.answer(f"[{clear_MD(course['name'])}]({clear_MD(url_to_course)})\n[{clear_MD(assign['name'])}]({clear_MD(url_to_assign)})\n\Text submitted\!", reply_markup=add_delete_button(), parse_mode='MarkdownV2')
    else:
        await message.answer(f"Error: {result[0]['message']}", reply_markup=add_delete_button())

    async with state.proxy() as data:
        await delete_msg(data['msg'], message)
    await state.finish()


@dp.throttled(trottle, rate=15)
@count_active_user
@Logger.log_msg
@login_required
async def update(message: types.Message, state: FSMContext):
    from ...app.api.router import insert_user, users
    users : list
    user_id = message.from_user.id

    if str(user_id) in users:
        users.remove(str(user_id))
    elif int(user_id) in users:
        users.remove(int(user_id))

    await insert_user(user_id)
    await message.reply("Wait, you're first in queue for an update", reply_markup=add_delete_button())
    await NotificationDB.set_notification_status(user_id, 'is_update_requested', True)


@dp.throttled(trottle, rate=30)
@count_active_user
@Logger.log_msg
@login_and_active_sub_required
async def check_finals(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await CourseDB.is_ready_courses(user_id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await message.answer(text, reply_markup=main_menu())
        return

    courses = await CourseDB.get_courses(user_id, True)
    try:
        text = ""
        for course in courses:
            midterm: Grade | None = course.grades.get('0', None)
            endterm: Grade | None = course.grades.get('1', None)
            term: Grade | None = course.grades.get('2', None)
            if not midterm or not endterm or not term:
                continue

            midterm_grade = str(str(midterm.percantage).replace(' %', '').replace(',', '.'))
            endterm_grade = str(str(endterm.percantage).replace(' %', '').replace(',', '.'))
            term_grade = str(str(term.percantage).replace(' %', '').replace(',', '.'))

            text += f"\n\n[{clear_MD(course['name'])}](https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course['id']})\n"
            text += f"    Reg MidTerm: {clear_MD(midterm_grade)}{'%' if midterm_grade.replace('.', '').isdigit() else ''}\n"
            text += f"    Reg EndTerm: {clear_MD(endterm_grade)}{'%' if endterm_grade.replace('.', '').isdigit() else ''}\n"
            text += f"    Reg Term: {clear_MD(term_grade)}{'%' if endterm_grade.replace('.', '').isdigit() else ''}\n"
            if midterm_grade != "-" and endterm_grade != "-" and midterm_grade != "Error" and endterm_grade != "Error":
                midterm_grade = float(midterm_grade)
                endterm_grade = float(endterm_grade)
                term_grade = float(term_grade)

                if midterm_grade >= 25 and endterm_grade >= 25 and term_grade >= 50:
                    save_1 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 50) * (100/40) * -1, 2)
                    save_2 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 70) * (100/40) * -1, 2)
                    save_3 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 90) * (100/40) * -1, 2)
                    save_4 = round((30/100*midterm_grade) + (30/100*endterm_grade) + 40, 2)

                    text += "\n    ⚫️ In order not to get a retake \(\>50\)\n"
                    if save_1 >= 100:
                        text += f"    Impossible\n"
                    elif save_1 >= 50:
                        text += f"    {clear_MD(str(save_1))}%\n"
                    elif save_1 < 50:
                        text += f"    50%\n"

                    text += "\n    🔴 To save the scholarship \(\>70\)\n"
                    if save_2 >= 50 and save_2 <= 100:
                        text += f"    {clear_MD(str(save_2))}%\n"
                    elif save_2 > 0 and save_2 < 50:
                        text += f"    50%\n"
                    else:
                        text += f"    Impossible\n"

                    text += "\n    🔵 To receive an enhanced scholarship \(\>90\)\n"
                    if save_3 >= 50 and save_3 <= 100:
                        text += f"    {clear_MD(str(save_3))}%\n"
                    elif save_3 > 0 and save_3 < 50:
                        text += f"    50%\n"
                    else:
                        text += f"    Impossible\n"

                    text += "\n    ⚪️ If you pass the Final 100%, you will get a Total:\n"
                    text += f"    {clear_MD(str(save_4))}%\n"
                elif midterm_grade < 25 or endterm_grade < 25 or term_grade < 50:
                    if midterm_grade < 25:
                        text += f'    ⚠️ Reg MidTerm less than 25%\n'
                    if endterm_grade < 25:
                        text += f'    ⚠️ Reg EndTerm less than 25%\n'
                    if term_grade < 50:
                        text += f'    ⚠️ Reg Term less than 50%\n'
        await message.answer(text, parse_mode="MarkdownV2")
    except Exception as exc:
        Logger.error(exc, exc_info=True)


def register_handlers_moodle(dp: Dispatcher):
    dp.register_message_handler(register, commands="register", state="*")
    dp.register_message_handler(wait_mail, content_types=['text'], state=MoodleForm.wait_mail)
    dp.register_message_handler(wait_api_token, content_types=['text'], state=MoodleForm.wait_api_token)

    dp.register_message_handler(submit_assign_show_courses, commands="submit_assignment", state="*")

    dp.register_message_handler(update, commands="update", state="*")

    dp.register_message_handler(check_finals, commands="check_finals", state="*")
    
    dp.register_message_handler(submit_assign_text, content_types=['text'], state=Submit.wait_text)
    dp.register_message_handler(submit_assign_file, content_types=['document'], state=Submit.wait_file)


    dp.register_callback_query_handler(
        register_moodle_query,
        lambda c: c.data == "register",
        state="*"
    )

    dp.register_callback_query_handler(
        get_grades,
        lambda c: c.data == "get_grades",
        state="*"
    )
    dp.register_callback_query_handler(
        get_grades_choose_course_text,
        lambda c: c.data.split()[0] == "get_grades",
        lambda c: c.data.split()[2] == "text",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )
    dp.register_callback_query_handler(
        get_grades_course_text,
        lambda c: c.data.split()[0] == "get_grades",
        lambda c: c.data.split()[2] == "text",
        lambda c: len(c.data.split()) == 4,
        state="*"
    )

    dp.register_callback_query_handler(
        get_deadlines,
        lambda c: c.data == "get_deadlines",
        state="*"
    )

    dp.register_callback_query_handler(
        get_deadlines_choose_courses,
        lambda c: c.data == "get_deadlines active",
        state="*"
    )
    dp.register_callback_query_handler(
        get_deadlines_course,
        lambda c: c.data.split()[0] == "get_deadlines",
        lambda c: c.data.split()[1] == "active",
        state="*"
    )

    dp.register_callback_query_handler(
        get_deadlines_choose_days,
        lambda c: c.data == "get_deadlines days",
        state="*"
    )
    dp.register_callback_query_handler(
        get_deadlines_days,
        lambda c: c.data.split()[0] == "get_deadlines",
        lambda c: c.data.split()[1] == "days",
        state="*"
    )

    dp.register_callback_query_handler(
        submit_assign_show_courses,
        lambda c: c.data == "submit_assign",
        state="*"
    )
    dp.register_callback_query_handler(
        submit_assign_cancel,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: c.data.split()[1] == "cancel",
        lambda c: len(c.data.split()) == 2,
        state="*"
    )
    dp.register_callback_query_handler(
        submit_assign_show_assigns,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 2,
        state="*"
    )
    dp.register_callback_query_handler(
        submit_assign_choose_type,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )
    dp.register_callback_query_handler(
        submit_assign_wait,
        lambda c: c.data.split()[0] == "submit_assign",
        lambda c: len(c.data.split()) == 4,
        state="*"
    )
