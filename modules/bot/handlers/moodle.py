import json
from datetime import datetime, timedelta
from typing import BinaryIO

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import dp, rate
from modules.bot.functions.rights import login_and_active_sub_required, login_required, active_sub_required

from ... import database
from ... import logger as Logger
from ...logger import logger
from ..functions.deadlines import (get_deadlines_local_by_course,
                                   get_deadlines_local_by_days)
from ..functions.functions import (clear_MD, delete_msg, save_submission,
                                   upload_file)
from ..functions.grades import local_grades
from ..keyboards.default import add_delete_button, main_menu
from ..keyboards.moodle import (active_att_btns, active_grades_btns, att_btns,
                                back_to_curriculum_trimester, back_to_get_att,
                                back_to_get_att_active, course_back,
                                deadlines_btns, deadlines_courses_btns,
                                deadlines_days_btns, grades_btns,
                                register_moodle_query, show_assigns_cancel_btn,
                                show_assigns_for_submit, show_assigns_type,
                                show_courses_for_submit,
                                show_curriculum_components,
                                show_curriculum_courses,
                                show_curriculum_trimesters)


class MoodleForm(StatesGroup):
    wait_barcode = State()
    wait_passwd = State()

class PDF_process(StatesGroup):
    busy = State()

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

    if not await database.if_user(user_id):
        await database.new_user(user_id)
    
    msg = await query.message.answer("Write your *barcode*:", parse_mode='MarkdownV2')
    await delete_msg(query.message)
    await MoodleForm.wait_barcode.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


@dp.throttled(rate=rate)
@Logger.log_msg
async def register_moodle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await database.if_user(user_id):
        await database.new_user(user_id)
    
    msg = await message.answer("Write your *barcode*:", parse_mode='MarkdownV2')
    await delete_msg(message)
    await MoodleForm.wait_barcode.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


@dp.throttled(rate=rate)
async def wait_barcode(message: types.Message, state: FSMContext):
    barcode = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)

    if not barcode.isdigit():
        msg = await message.answer('Error\! Write your *barcode* one more time:', parse_mode='MarkdownV2')
    else:
        msg = await message.answer("Write your *password*:", parse_mode='MarkdownV2')
        await MoodleForm.wait_passwd.set()

    async with state.proxy() as data:
        data['barcode'] = barcode
        data['msg_del'] = msg


@dp.throttled(rate=rate)
async def wait_password(message: types.Message, state: FSMContext):
    from ...app.api.router import users
    users : list
    user_id = message.from_user.id
    passwd = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)

    if len(passwd.split()) > 1:
        msg = await message.answer('Error\! Write your *password* one more time:', parse_mode='MarkdownV2')
        async with state.proxy() as data:
            data['msg_del'] = msg
    else:    
        async with state.proxy() as data:
            barcode = data['barcode']
        await database.user_register_moodle(user_id, barcode, passwd)
        if str(user_id) in users:
            users.remove(str(user_id))
        users.insert(0, str(user_id))

        text = "Your Moodle account is registered\!"
        if not await database.is_active_sub(user_id):
            text += "\n\nAvailable functions:\n" \
                    "\- Grades \(without notifications\)\n\n" \
                    "To get access to all the features you need to purchase a subscription"
        
        await message.answer(text, parse_mode='MarkdownV2', reply_markup=main_menu())
        await state.finish()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_grades(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await database.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = "Choose option:"
        await query.message.edit_text(text, reply_markup=grades_btns())
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await database.is_ready_courses(message.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        text = "Choose option:"
        await message.answer(text, reply_markup=grades_btns())


@dp.throttled(rate=rate)
@Logger.log_msg
@login_required
async def get_grades_pdf(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if await state.get_state() == 'Form:busy':
        await query.answer('Wait until you receive a response from the previous request')
        return
    
    await PDF_process.busy.set()
    try:
        user = await database.get_dict(user_id)
        try:
            user['courses'] = json.loads(user['courses'])
        except:
            ...
        if query.data.split()[1] == 'active':
            is_active_only = True
        else:
            is_active_only = False
        await query.answer('Wait')
        await local_grades(user, query.message, is_active_only)
    except Exception as exc:
        logger.error(exc, exc_info=True)
        await query.answer('Error, write Admin to check and solve this')
    await state.finish()


@dp.throttled(rate=rate)
@login_required
async def get_grades_choose_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    is_active = True if query.data.split()[1] == 'active' else False
    text = "Choose one:"
    courses = json.loads(await database.get_key(user_id, 'courses'))
    kb = active_grades_btns(courses, is_active)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
@login_required
async def get_grades_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    user_id = query.from_user.id
    is_active = True if query.data.split()[1] == 'active' else False
    courses = json.loads(await database.get_key(user_id, 'courses'))
    course_id = query.data.split()[3]
    course = courses[course_id]
    course_name = course['name']

    text = f"[{clear_MD(course_name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course_id}')})\n"
    for grade_id, grade in course['grades'].items():
        name = grade['name']
        percentage = clear_MD(grade['percentage'])
        if '%' in percentage:
            percentage = f"*{percentage}*"
        text += f"    {clear_MD(name)}  \-  {percentage}\n"

    kb = course_back(is_active)
    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_deadlines(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await database.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = "Choose filter for deadlines:"
        await query.message.edit_text(text, reply_markup=deadlines_btns())
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await database.is_ready_courses(message.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        text = "Choose one option:"
        await message.answer(text, reply_markup=deadlines_btns())


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_deadlines_choose_courses(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    user = await database.get_dict(query.from_user.id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_courses_btns(user['courses']))


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_deadlines_course(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    user = await database.get_dict(user_id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...

    id = int(query.data.split()[2])
    text = await get_deadlines_local_by_course(user, id)

    await query.message.answer(text, parse_mode='Markdown', reply_markup=add_delete_button())
    await query.answer()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_deadlines_choose_days(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_days_btns())


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_deadlines_days(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    user = await database.get_dict(user_id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...

    days = int(query.data.split()[2])
    text = await get_deadlines_local_by_days(user, days)

    await query.message.answer(text, parse_mode='Markdown', reply_markup=add_delete_button())
    await query.answer()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_gpa(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await database.is_ready_gpa(query.from_user.id):
            text = "Your GPA are not ready, you are in queue, try later. If there will be some error, we will notify\n\n" \
                "If you haven't finished the first trimester, it won't be shown either"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = await database.get_gpa_text(query.from_user.id)
        await query.message.edit_text(text, reply_markup=main_menu(), parse_mode='MarkdownV2')
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await database.is_ready_gpa(message.from_user.id):
            text = "Your GPA are not ready, you are in queue, try later. If there will be some error, we will notify\n\n" \
                    "If you haven't finished the first trimester, it won't be shown either"
            await message.answer(text, reply_markup=main_menu())
            return

        text = await database.get_gpa_text(query.from_user.id)
        await message.answer(text, reply_markup=main_menu(), parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_att_choose(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await database.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        await query.message.edit_text('Choose one:', reply_markup=att_btns())

    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await database.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        await message.answer('Choose one:', reply_markup=att_btns())


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def get_att(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    arg = query.data.split()[1]

    if arg == 'total':
        att = json.loads(await database.get_key(user_id, 'att_statistic'))
        text = "Your Total Attendance:\n\n"
        for key, value in att.items():
            text += f"{clear_MD(key)} \= *{clear_MD(value)}*\n"
        await query.message.edit_text(text, reply_markup=back_to_get_att(), parse_mode='MarkdownV2')
    if arg == 'active':
        courses = json.loads(await database.get_key(user_id, 'courses'))
        await query.message.edit_text('Choose one:', reply_markup=active_att_btns(courses))


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def get_att_course(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    arg = query.data.split()[2]

    courses = json.loads(await database.get_key(user_id, 'courses'))
    course_name = courses[arg]['name']
    course_id = courses[arg]['id']

    text = f"[{clear_MD(course_name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course_id}')})\n\n"
    for key, value in courses[arg]['attendance'].items():
        text += f"{clear_MD(key)}: *{clear_MD(value)}*\n"

    await query.message.edit_text(text, reply_markup=back_to_get_att_active(), parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def submit_assign_show_courses(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        user_id = query.from_user.id

        courses = json.loads(await database.get_key(user_id, 'courses'))

        text = f"Choose one:"
        await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    elif query.__class__ is types.Message:
        message : types.Message = query
        user_id = message.from_user.id

        courses = json.loads(await database.get_key(user_id, 'courses'))

        await message.answer("Choose one:", reply_markup=show_courses_for_submit(courses))


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_cancel(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    courses = json.loads(await database.get_key(user_id, 'courses'))

    text = f"Choose one:"
    await query.message.edit_text(text, reply_markup=show_courses_for_submit(courses))
    await state.finish()


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_show_assigns(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    course_id = query.data.split()[1]
    
    courses = json.loads(await database.get_key(user_id, 'courses'))

    assigns = courses[course_id]['assignments']

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

    msg = await query.message.edit_text(text, reply_markup=show_assigns_cancel_btn(course_id))

    async with state.proxy() as data:
        data['course_id'] = course_id
        data['assign_id'] = assign_id
        data['type'] = type
        data['msg'] = msg


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_file(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        course_id = data['course_id']
        assign_id = data['assign_id']

    courses = json.loads(await database.get_key(message.from_user.id, 'courses'))
    course = courses[course_id]
    assign = courses[course_id]['assignments'][assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course['id']}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign['id']}"

    token = await database.get_key(message.from_user.id, 'token')
    
    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    file_name = file_path.split('/')[-1]

    my_object = None
    file_to_upload = await message.bot.download_file(file_path, my_object)

    data_file = await upload_file(file_to_upload, file_name, token)
    item_id = data_file[0]['itemid']
    result = await save_submission(token, assign['assign_id'], item_id=item_id)
    if result == []:
        await message.answer(f"[{clear_MD(course['name'])}]({clear_MD(url_to_course)})\n[{clear_MD(assign['name'])}]({clear_MD(url_to_assign)})\n\nFile submitted\!", reply_markup=add_delete_button(), parse_mode='MarkdownV2')
    else:
        if type(result) is list:
            await message.answer(f"Error: {result[0].get('item', None)}\n{result[0].get('message', None)}", reply_markup=add_delete_button())
        else:
            await message.answer(f"Error: {result.get('item', None)}\n{result.get('message', None)}", reply_markup=add_delete_button())

    async with state.proxy() as data:
        await delete_msg(data['msg'], message)


@dp.throttled(rate=rate)
@login_and_active_sub_required
async def submit_assign_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        course_id = data['course_id']
        assign_id = data['assign_id']

    courses = json.loads(await database.get_key(message.from_user.id, 'courses'))
    course = courses[course_id]
    assign = courses[course_id]['assignments'][assign_id]

    url_to_course = f"https://moodle.astanait.edu.kz/course/view.php?id={course['id']}"
    url_to_assign = f"https://moodle.astanait.edu.kz/mod/assign/view.php?id={assign['id']}"

    token = await database.get_key(message.from_user.id, 'token')
    
    result = await save_submission(token, assign['assign_id'], text=message.text)
    if result == []:
        await message.answer(f"[{clear_MD(course['name'])}]({clear_MD(url_to_course)})\n[{clear_MD(assign['name'])}]({clear_MD(url_to_assign)})\n\Text submitted\!", reply_markup=add_delete_button(), parse_mode='MarkdownV2')
    else:
        await message.answer(f"Error: {result[0]['message']}", reply_markup=add_delete_button())

    async with state.proxy() as data:
        await delete_msg(data['msg'], message)


@dp.throttled(trottle, rate=15)
@Logger.log_msg
@login_required
async def update(message: types.Message, state: FSMContext):
    from ...app.api.router import users
    users : list
    user_id = message.from_user.id

    if str(user_id) in users:
        users.remove(str(user_id))
    elif int(user_id) in users:
        users.remove(int(user_id))

    args = ['message', 'message_end_date']
    await database.redis.hdel(user_id, *args)
    await database.redis.hset(user_id, 'ignore', 2)
    users.insert(0, str(user_id))
    await message.reply("Wait, you're first in queue for an update", reply_markup=add_delete_button())


@dp.throttled(trottle, rate=45)
@Logger.log_msg
@login_required
async def update_full(message: types.Message, state: FSMContext):
    from ...app.api.router import users
    users : list
    user_id = message.from_user.id

    if str(user_id) in users:
        users.remove(str(user_id))
    elif int(user_id) in users:
        users.remove(int(user_id))

    
    args = ['cookies', 'token', 'message', 'message_end_date', 'curriculum', 'att_statistic', 'courses', 'gpa']
    await database.redis.hdel(user_id, *args)
    await database.redis.hset(user_id, 'ignore', 1)
    users.insert(0, str(user_id))
    await message.reply("Wait, you're first in queue for an update", reply_markup=add_delete_button())


@dp.throttled(trottle, rate=30)
@Logger.log_msg
@login_and_active_sub_required
async def check_finals(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await database.is_ready_courses(user_id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await message.answer(text, reply_markup=main_menu())
        return

    courses = json.loads(await database.get_key(user_id, 'courses'))
    courses = list(filter(lambda course: course['active'] is True, courses.values()))
    try:
        text = ""
        for course in courses:
            mid = course['grades'].get('0', None)
            end = course['grades'].get('1', None)
            term = course['grades'].get('2', None)
            if not mid or not end or not term:
                continue

            midterm_grade = str(str(mid['percentage']).replace(' %', '').replace(',', '.'))
            endterm_grade = str(str(end['percentage']).replace(' %', '').replace(',', '.'))
            term_grade = str(str(term['percentage']).replace(' %', '').replace(',', '.'))

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
        logger.error(exc, exc_info=True)


@dp.throttled(rate=0.5)
@Logger.log_msg
@login_and_active_sub_required
async def get_curriculum(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await database.is_ready_curriculum(query.from_user.id):
            text = "Your curriculum are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        await query.message.edit_text("Choose one:", reply_markup=show_curriculum_courses())
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await database.is_ready_courses(query.from_user.id):
            text = "Your curriculum are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        await message.answer("Choose one:", reply_markup=show_curriculum_courses())


@dp.throttled(rate=0.5)
@Logger.log_msg
@login_and_active_sub_required
async def get_curriculum_trimesters(query: types.CallbackQuery, state: FSMContext):
    course = query.data.split()[1]
    await query.message.edit_text("Choose one:", reply_markup=show_curriculum_trimesters(course))


@dp.throttled(rate=0.5)
@Logger.log_msg
@login_and_active_sub_required
async def get_curriculum_components(query: types.CallbackQuery, state: FSMContext):
    course = query.data.split()[1]
    trimester = query.data.split()[2]
    curriculum = json.loads(await database.redis.hget(query.from_user.id, 'curriculum'))
    components = curriculum[course][trimester]
    await query.message.edit_text("Choose one:", reply_markup=show_curriculum_components(course, trimester, components))


@dp.throttled(rate=0.5)
@Logger.log_msg
@login_and_active_sub_required
async def get_curriculum_show_component(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_curriculum(query.from_user.id):
        text = "Your curriculum are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return
    course = query.data.split()[1]
    trimester = query.data.split()[2]
    id = query.data.split()[3]
    curriculum = json.loads(await database.redis.hget(query.from_user.id, 'curriculum'))
    component = curriculum[course][trimester][id]
    text = f"{component['name']}\n" \
            f"Credits: {component['credits']}"
    await query.message.edit_text(text, reply_markup=back_to_curriculum_trimester(course, trimester))


def register_handlers_moodle(dp: Dispatcher):
    dp.register_message_handler(register_moodle, commands="register_moodle", state="*")
    dp.register_message_handler(wait_barcode, content_types=['text'], state=MoodleForm.wait_barcode)
    dp.register_message_handler(wait_password, content_types=['text'], state=MoodleForm.wait_passwd)

    dp.register_message_handler(get_grades, commands="get_grades", state="*")
    dp.register_message_handler(get_deadlines, commands="get_deadlines", state="*")

    dp.register_message_handler(get_gpa, commands="get_gpa", state="*")
    # dp.register_message_handler(get_att_choose, commands="get_attendance", state="*")
    
    dp.register_message_handler(submit_assign_show_courses, commands="submit_assignment", state="*")

    dp.register_message_handler(update, commands="update", state="*")
    dp.register_message_handler(update_full, commands="update_full", state="*")

    dp.register_message_handler(check_finals, commands="check_finals", state="*")
    
    dp.register_message_handler(get_curriculum, commands="get_curriculum", state="*")

    dp.register_message_handler(submit_assign_text, content_types=['text'], state=Submit.wait_text)
    dp.register_message_handler(submit_assign_file, content_types=['document'], state=Submit.wait_file)


    dp.register_callback_query_handler(
        register_moodle_query,
        lambda c: c.data == "register_moodle",
        state="*"
    )

    dp.register_callback_query_handler(
        get_grades,
        lambda c: c.data == "get_grades",
        state="*"
    )
    dp.register_callback_query_handler(
        get_grades_pdf,
        lambda c: c.data.split()[0] == "get_grades",
        lambda c: c.data.split()[2] == "pdf",
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
        get_gpa,
        lambda c: c.data == "get_gpa",
        state="*"
    )

    # dp.register_callback_query_handler(
    #     get_att_choose,
    #     lambda c: c.data == "get_att",
    #     state="*"
    # )
    # dp.register_callback_query_handler(
    #     get_att,
    #     lambda c: c.data.split()[0] == "get_att",
    #     lambda c: len(c.data.split()) == 2,
    #     state="*"
    # )
    # dp.register_callback_query_handler(
    #     get_att_course,
    #     lambda c: c.data.split()[0] == "get_att",
    #     lambda c: c.data.split()[1] == "active",
    #     lambda c: len(c.data.split()) == 3,
    #     state="*"
    # )

    # dp.register_callback_query_handler(
    #     submit_assign_show_courses,
    #     lambda c: c.data == "submit_assign",
    #     state="*"
    # )
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

    dp.register_callback_query_handler(
        get_curriculum,
        lambda c: c.data == "get_curriculum",
        state="*"
    )
    dp.register_callback_query_handler(
        get_curriculum_trimesters,
        lambda c: c.data.split()[0] == "get_curriculum",
        lambda c: len(c.data.split()) == 2,
        state="*"
    )
    dp.register_callback_query_handler(
        get_curriculum_components,
        lambda c: c.data.split()[0] == "get_curriculum",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )
    dp.register_callback_query_handler(
        get_curriculum_show_component,
        lambda c: c.data.split()[0] == "get_curriculum",
        lambda c: len(c.data.split()) == 4,
        state="*"
    )
