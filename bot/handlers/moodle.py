import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.functions.deadlines import get_deadlines_local

from bot.functions.functions import delete_msg
from bot.functions.grades import local_grades
from bot.objects.logger import print_msg
from bot.keyboards.default import add_delete_button, main_menu
from bot.keyboards.moodle import (deadlines_btns, grades_btns,
                                  register_moodle_query, sub_buttons)
from bot.objects import aioredis


class MoodleForm(StatesGroup):
    wait_barcode = State()
    wait_passwd = State()


@print_msg
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


@print_msg
async def register_moodle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
    
    msg = await message.answer("Write your *barcode*:", parse_mode='MarkdownV2')
    await delete_msg(message)
    await MoodleForm.wait_barcode.set()

    async with state.proxy() as data:
        data['msg_del'] = msg


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


async def wait_password(message: types.Message, state: FSMContext):
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
        await message.answer("Your Moodle account is registred\!", parse_mode='MarkdownV2', reply_markup=main_menu())
        await state.finish()


async def sub_menu_query(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_text('Choose and click:', reply_markup=kb)


@print_msg
async def sub_grades(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    await aioredis.sub_on_mailing(user_id, 'grades_sub', int(query.data.split()[1]))
    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_reply_markup(reply_markup=kb)   


@print_msg
async def sub_deadlines(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    await aioredis.sub_on_mailing(user_id, 'deadlines_sub', int(query.data.split()[1]))
    sub_grades, sub_deadlines = await aioredis.get_mailing_sub(user_id)
    kb = sub_buttons(sub_grades, sub_deadlines)    
    await query.message.edit_reply_markup(reply_markup=kb) 


@print_msg
async def get_grades_choose(query: types.CallbackQuery, state: FSMContext):
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


@print_msg
async def get_grades(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    
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


@print_msg
async def get_deadlines_choose(query: types.CallbackQuery, state: FSMContext):
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

        text = "Choose filter for deadlines:"
        await message.answer(text, reply_markup=deadlines_btns())


@print_msg
async def get_deadlines(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    if not await aioredis.if_user(user_id):
        await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_registered_moodle(user_id):
        await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
        return
    if not await aioredis.is_active_sub(user_id):
        await query.message.edit_text("Your subscription is not active. /purchase or /demo", reply_markup=main_menu())
        return
    
    user = await aioredis.get_dict(user_id)
    try:
        user['courses'] = json.loads(user['courses'])
    except:
        ...

    days = int(query.data.split()[1])
    text = await get_deadlines_local(user, days)

    await query.message.answer(text, parse_mode='Markdown', reply_markup=add_delete_button())
    await query.answer()


@print_msg
async def get_gpa(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        user_id = query.from_user.id
        if not await aioredis.if_user(user_id):
            await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await query.message.edit_text("First you nedd to /register_moodle", reply_markup=main_menu())
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
            await message.answer("First you nedd to /register_moodle", reply_markup=main_menu())
            return
        if not await aioredis.is_registered_moodle(user_id):
            await message.answer("First you nedd to /register_moodle", reply_markup=main_menu())
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


def register_handlers_moodle(dp: Dispatcher):
    dp.register_message_handler(register_moodle, commands="register_moodle", state="*")
    dp.register_message_handler(wait_barcode, content_types=['text'], state=MoodleForm.wait_barcode)
    dp.register_message_handler(wait_password, content_types=['text'], state=MoodleForm.wait_passwd)

    dp.register_message_handler(get_grades_choose, commands="get_grades", state="*")
    dp.register_message_handler(get_deadlines_choose, commands="get_deadlines", state="*")

    dp.register_message_handler(get_gpa, commands="get_gpa", state="*")

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
        get_grades_choose,
        lambda c: c.data == "get_grades",
        state="*"
    )
    dp.register_callback_query_handler(
        get_grades,
        lambda c: c.data.split()[0] == "get_grades",
        state="*"
    )

    dp.register_callback_query_handler(
        get_deadlines_choose,
        lambda c: c.data == "get_deadlines",
        state="*"
    )
    dp.register_callback_query_handler(
        get_deadlines,
        lambda c: c.data.split()[0] == "get_deadlines",
        state="*"
    )

    dp.register_callback_query_handler(
        get_gpa,
        lambda c: c.data == "get_gpa",
        state="*"
    )
