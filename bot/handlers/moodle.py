import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.functions.deadlines import get_deadlines_local_by_course, get_deadlines_local_by_days

from bot.functions.functions import clear_MD, delete_msg
from bot.functions.grades import local_grades
from bot.objects.logger import log_msg
from bot.keyboards.default import add_delete_button, main_menu
from bot.keyboards.moodle import (active_att_btns, active_grades_btns, att_btns, back_to_get_att, back_to_get_att_active, course_back, deadlines_btns, deadlines_courses_btns, deadlines_days_btns, grades_btns,
                                  register_moodle_query, sub_buttons)
from bot.objects import aioredis
from bot.objects.logger import logger
from config import dp, rate


class MoodleForm(StatesGroup):
    wait_barcode = State()
    wait_passwd = State()

class Form(StatesGroup):
    busy = State()


@dp.throttled(rate=5)
async def trottle(*args, **kwargs):
    message = args[0]
    rate = kwargs['rate']

    if message.__class__ is types.Message:
        await message.answer(f"Not so fast, wait {rate} seconds\n\nSome commands cannot be called frequently")
    elif message.__class__ is types.CallbackQuery:
        await message.answer(f"Not so fast, wait {rate} seconds")
    

@dp.throttled(rate=rate)
@log_msg
async def register_moodle_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
    
    msg = await query.message.answer("Write your *barcode*:", parse_mode='MarkdownV2')
    await delete_msg(query.message)
    await MoodleForm.wait_barcode.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


@dp.throttled(rate=rate)
@log_msg
async def register_moodle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
    
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
    from app.api.router import users
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
        await aioredis.user_register_moodle(user_id, barcode, passwd)
        if str(user_id) in users:
            users.remove(str(user_id))
        users.insert(0, str(user_id))
        await message.answer("Your Moodle account is registred\!", parse_mode='MarkdownV2', reply_markup=main_menu())
        await state.finish()


@dp.throttled(rate=rate)
async def sub_menu_query(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_text('Choose and click:', reply_markup=kb)


@dp.throttled(rate=rate)
@log_msg
async def sub_grades(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    await aioredis.sub_on_mailing(user_id, 'grades_sub', int(query.data.split()[1]))
    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_reply_markup(reply_markup=kb)   


@dp.throttled(rate=rate)
@log_msg
async def sub_deadlines(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    await aioredis.sub_on_mailing(user_id, 'deadlines_sub', int(query.data.split()[1]))
    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_reply_markup(reply_markup=kb) 


@dp.throttled(rate=rate)
@log_msg
async def get_grades(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await aioredis.is_registered_moodle(query.from_user.id):
            text = "First you need to /register_moodle"
            await query.message.edit_text(text, reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = "Choose option:"
        await query.message.edit_text(text, reply_markup=grades_btns())
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await aioredis.is_registered_moodle(message.from_user.id):
            text = "First you need to /register_moodle"
            await message.answer(text, reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(message.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        text = "Choose option:"
        await message.answer(text, reply_markup=grades_btns())


@dp.throttled(rate=rate)
@log_msg
async def get_grades_pdf(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if await state.get_state() == 'Form:busy':
        await query.answer('Wait until you receive a response from the previous request')
        return
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    
    await Form.busy.set()
    try:
        user = await aioredis.get_dict(user_id)
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
async def get_grades_choose_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    is_active = True if query.data.split()[1] == 'active' else False
    text = "Choose one:"
    courses = json.loads(await aioredis.get_key(user_id, 'courses'))
    kb = active_grades_btns(courses, is_active)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def get_grades_course_text(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return

    user_id = query.from_user.id
    is_active = True if query.data.split()[1] == 'active' else False
    courses = json.loads(await aioredis.get_key(user_id, 'courses'))
    course_id = query.data.split()[3]
    course = courses[course_id]
    course_name = course['name']

    text = f"[{clear_MD(course_name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course_id}')})\n"
    for grade_id, grade in course['grades'].items():
        name = grade['name']
        percentage = grade['percentage']
        text += f"    {clear_MD(name)}  \-  {clear_MD(percentage)}\n"

    kb = course_back(is_active)
    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@log_msg
async def get_deadlines(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        if not await aioredis.is_registered_moodle(query.from_user.id):
            text = "First you need to /register_moodle"
            await query.message.edit_text(text, reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = "Choose filter for deadlines:"
        await query.message.edit_text(text, reply_markup=deadlines_btns())
    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await aioredis.is_registered_moodle(message.from_user.id):
            text = "First you need to /register_moodle"
            await message.answer(text, reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(message.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        text = "Choose one option:"
        await message.answer(text, reply_markup=deadlines_btns())


@dp.throttled(rate=rate)
@log_msg
async def get_deadlines_choose_courses(query: types.CallbackQuery, state: FSMContext):
    if not await aioredis.is_registered_moodle(query.from_user.id):
        text = "First you need to /register_moodle"
        await query.message.edit_text(text, reply_markup=main_menu())
        return
    if not await aioredis.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    user = await aioredis.get_dict(query.from_user.id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...
    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_courses_btns(user['courses']))


@dp.throttled(rate=rate)
@log_msg
async def get_deadlines_course(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    
    user = await aioredis.get_dict(user_id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...

    id = int(query.data.split()[2])
    text = await get_deadlines_local_by_course(user, id)

    await query.message.answer(text, parse_mode='Markdown', reply_markup=add_delete_button())
    await query.answer()


@dp.throttled(rate=rate)
@log_msg
async def get_deadlines_choose_days(query: types.CallbackQuery, state: FSMContext):
    if not await aioredis.is_registered_moodle(query.from_user.id):
        text = "First you need to /register_moodle"
        await query.message.edit_text(text, reply_markup=main_menu())
        return
    if not await aioredis.is_ready_courses(query.from_user.id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    text = "Choose filter for deadlines:"
    await query.message.edit_text(text, reply_markup=deadlines_days_btns())


@dp.throttled(rate=rate)
@log_msg
async def get_deadlines_days(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    
    user = await aioredis.get_dict(user_id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...

    days = int(query.data.split()[2])
    text = await get_deadlines_local_by_days(user, days)

    await query.message.answer(text, parse_mode='Markdown', reply_markup=add_delete_button())
    await query.answer()


@dp.throttled(rate=rate)
@log_msg
async def get_gpa(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        user_id = query.from_user.id
        if not await aioredis.if_user(user_id):
            await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_active_sub(user_id):
            await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
            return

        if not await aioredis.is_ready_gpa(query.from_user.id):
            text = "Your GPA are not ready, you are in queue, try later. If there will be some error, we will notify\n\n" \
                "If you haven't finished the first trimester, it won't be shown either"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        text = await aioredis.get_gpa_text(query.from_user.id)
        await query.message.edit_text(text, reply_markup=main_menu(), parse_mode='MarkdownV2')
    elif query.__class__ is types.Message:
        message : types.Message = query
        user_id = message.from_user.id
        if not await aioredis.if_user(user_id):
            await message.answer("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await message.answer("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_active_sub(user_id):
            await message.answer("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
            return
        if not await aioredis.is_ready_gpa(message.from_user.id):
            text = "Your GPA are not ready, you are in queue, try later. If there will be some error, we will notify\n\n" \
                    "If you haven't finished the first trimester, it won't be shown either"
            await message.answer(text, reply_markup=main_menu())
            return

        text = await aioredis.get_gpa_text(query.from_user.id)
        await message.answer(text, reply_markup=main_menu(), parse_mode='MarkdownV2')


@dp.throttled(rate=rate)
@log_msg
async def get_att_choose(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if query.__class__ is types.CallbackQuery:
        if not await aioredis.if_user(user_id):
            await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await query.message.edit_text("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_active_sub(user_id):
            await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await query.message.edit_text(text, reply_markup=main_menu())
            return

        await query.message.edit_text('Choose one:', reply_markup=att_btns())

    elif query.__class__ is types.Message:
        message : types.Message = query
        if not await aioredis.if_user(user_id):
            await message.answer("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await message.answer("First you need to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_active_sub(user_id):
            await message.answer("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
            return
        if not await aioredis.is_ready_courses(query.from_user.id):
            text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
            await message.answer(text, reply_markup=main_menu())
            return

        await message.answer('Choose one:', reply_markup=att_btns())


@dp.throttled(rate=rate)
async def get_att(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    arg = query.data.split()[1]

    if arg == 'total':
        att = json.loads(await aioredis.get_key(user_id, 'att_statistic'))
        text = "Your Total Attendance:\n\n"
        for key, value in att.items():
            text += f"{key} = {value}\n"
        await query.message.edit_text(text, reply_markup=back_to_get_att())
    if arg == 'active':
        courses = json.loads(await aioredis.get_key(user_id, 'courses'))
        await query.message.edit_text('Choose one:', reply_markup=active_att_btns(courses))


@dp.throttled(rate=rate)
async def get_att_course(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    arg = query.data.split()[2]

    courses = json.loads(await aioredis.get_key(user_id, 'courses'))
    
    text = f"{courses[arg]['name']}\n\n"
    for key, value in courses[arg]['attendance'].items():
        text += f"{key}: {value}\n"

    await query.message.edit_text(text, reply_markup=back_to_get_att_active())


@dp.throttled(trottle, rate=60)
@log_msg
async def update(message: types.Message, state: FSMContext):
    from app.api.router import users
    users : list
    user_id = message.from_user.id

    if str(user_id) in users:
        users.remove(str(user_id))
    if int(user_id) in users:
        users.remove(int(user_id))
    users.insert(0, str(user_id))
    await message.answer("Wait, you're first in queue for an update")


@dp.throttled(trottle, rate=30)
@log_msg
async def check_finals(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await aioredis.if_user(user_id):
        await message.answer("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await message.answer("First you need to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await message.answer("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    if not await aioredis.is_ready_courses(user_id):
        text = "Your courses are not ready, you are in queue, try later. If there will be some error, we will notify"
        await message.answer(text, reply_markup=main_menu())
        return

    courses = json.loads(await aioredis.get_key(user_id, 'courses'))
    courses = list(filter(lambda course: course['active'] is True, courses.values()))
    try:
        text = ""
        for course in courses:
            mid = course['grades'].get('0', None)
            end = course['grades'].get('1', None)
            if not mid or not end:
                continue

            midterm_grade = str(str(mid['percentage']).replace(' %', '').replace(',', '.'))
            endterm_grade = str(str(end['percentage']).replace(' %', '').replace(',', '.'))

            text += f"\n\n[{clear_MD(course['name'])}](https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course['id']})\n"
            text += f"    MidTerm: {clear_MD(midterm_grade)}{'%' if midterm_grade.replace('.', '').isdigit() else ''}\n"
            text += f"    EndTerm: {clear_MD(endterm_grade)}{'%' if endterm_grade.replace('.', '').isdigit() else ''}\n"
            if midterm_grade != "-" and endterm_grade != "-" and midterm_grade != "Error" and endterm_grade != "Error":
                midterm_grade = float(midterm_grade)
                endterm_grade = float(endterm_grade)

                if midterm_grade>=25 and endterm_grade>=25:
                    save_1 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 50) * (100/40) * -1, 2)
                    save_2 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 70) * (100/40) * -1, 2)
                    save_3 = round(((30/100*midterm_grade) + (30/100*endterm_grade) - 90) * (100/40) * -1, 2)
                    save_4 = round((30/100*midterm_grade) + (30/100*endterm_grade) + 40, 2)

                    text += "\n    ⚫️ Чтобы не получить ретейк или пересдачу \(\>50\)\n"
                    if save_1 >= 100:
                        text += f"    Невозможно\n"
                    elif save_1 >= 50:
                        text += f"    {clear_MD(str(save_1))}%\n"
                    elif save_1 < 50:
                        text += f"    50%\n"

                    text += "\n    🔴 Для сохранения стипендии \(\>70\)\n"
                    if save_2 >= 50 and save_2 <= 100:
                        text += f"    {clear_MD(str(save_2))}%\n"
                    elif save_2 > 0 and save_2 < 50:
                        text += f"    50%\n"
                    else:
                        text += f"    Невозможно\n"

                    text += "\n    🔵 Для получения повышенной стипендии \(\>90\)\n"
                    if save_3 >= 50 and save_3 <= 100:
                        text += f"    {clear_MD(str(save_3))}%\n"
                    elif save_3 > 0 and save_3 < 50:
                        text += f"    50%\n"
                    else:
                        text += f"    Невозможно\n"

                    text += "\n    ⚪️ Если вы сдадите файнал на 100%, вы получите тотал:\n"
                    text += f"    {clear_MD(str(save_4))}%\n"
                elif midterm_grade<25 or endterm_grade<25:
                    if midterm_grade<25:
                        text += f'    ⚠️ MidTerm меньше 25%\n'
                    elif endterm_grade<25:
                        text += f'    ⚠️ EndTerm меньше 25%\n'
        await message.answer(text, parse_mode="MarkdownV2")
    except Exception as exc:
        logger.error(exc, exc_info=True)


def register_handlers_moodle(dp: Dispatcher):
    dp.register_message_handler(register_moodle, commands="register_moodle", state="*")
    dp.register_message_handler(wait_barcode, content_types=['text'], state=MoodleForm.wait_barcode)
    dp.register_message_handler(wait_password, content_types=['text'], state=MoodleForm.wait_passwd)

    dp.register_message_handler(get_grades, commands="get_grades", state="*")
    dp.register_message_handler(get_deadlines, commands="get_deadlines", state="*")

    dp.register_message_handler(get_gpa, commands="get_gpa", state="*")
    dp.register_message_handler(get_att_choose, commands="get_attendance", state="*")

    dp.register_message_handler(update, commands="update", state="*")
    dp.register_message_handler(check_finals, commands="check_finals", state="*")

    dp.register_callback_query_handler(
        register_moodle_query,
        lambda c: c.data == "register_moodle",
        state="*"
    )

    dp.register_callback_query_handler(
        sub_menu_query,
        lambda c: c.data == "sub_menu",
        state="*"
    )
    dp.register_callback_query_handler(
        sub_grades,
        lambda c: c.data.split()[0] == "sub_grades",
        state="*"
    )
    dp.register_callback_query_handler(
        sub_deadlines,
        lambda c: c.data.split()[0] == "sub_deadlines",
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

    dp.register_callback_query_handler(
        get_att_choose,
        lambda c: c.data == "get_att",
        state="*"
    )
    dp.register_callback_query_handler(
        get_att,
        lambda c: c.data.split()[0] == "get_att",
        lambda c: len(c.data.split()) == 2,
        state="*"
    )
    dp.register_callback_query_handler(
        get_att_course,
        lambda c: c.data.split()[0] == "get_att",
        lambda c: c.data.split()[1] == "active",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )
