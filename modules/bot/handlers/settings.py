import json
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from config import dp, rate
from modules.scheduler import EventsScheduler

from ...database import DB
from ... import logger as Logger
from ..handlers.moodle import trottle
from ..keyboards.settings import settings_btns


@dp.throttled(rate=rate)
@Logger.log_msg
async def settings(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    sleep_status = await DB.is_sleep(user_id)
    att_notify = await DB.redis.hget(user_id, 'att_notify')
    calendar_settings = await DB.redis.hget(user_id, 'calendar_settings')
    if not calendar_settings:
        calendar_settings = {}
        calendar_settings['diff_time'] = 5
        calendar_settings['notify'] = 0
    else:
        calendar_settings = json.loads(calendar_settings)
    if att_notify is None:
        att_notify = 1
    else:
        att_notify = int(att_notify)

    await query.message.edit_text('Set settings:', reply_markup=settings_btns(sleep_status, calendar_settings['notify']))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
async def sleep(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    if query.data == 'sleep':
        await DB.set_key(user_id, 'sleep', 1)
    elif query.data == 'awake':
        await DB.set_key(user_id, 'sleep', 0)

    sleep_status = await DB.is_sleep(user_id)
    att_notify = await DB.redis.hget(user_id, 'att_notify')
    calendar_settings = await DB.redis.hget(user_id, 'calendar_settings')
    if not calendar_settings:
        calendar_settings = {}
        calendar_settings['diff_time'] = 5
        calendar_settings['notify'] = 0
    else:
        calendar_settings = json.loads(calendar_settings)
    if att_notify is None:
        att_notify = 1
    else:
        att_notify = int(att_notify)

    await query.message.edit_reply_markup(reply_markup=settings_btns(sleep_status, calendar_settings['notify']))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
async def calendar_notify(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    calendar_settings = await DB.redis.hget(user_id, 'calendar_settings')
    if not calendar_settings:
        calendar_settings = {}
        calendar_settings['diff_time'] = 5
        calendar_settings['notify'] = 0
    else:
        calendar_settings = json.loads(calendar_settings)

    if query.data.split()[1] == '1':
        calendar_settings['notify'] = 1
        func = EventsScheduler.get_calendar_and_add_events
    elif query.data.split()[1] == '0':
        calendar_settings['notify'] = 0
        func =  EventsScheduler.delete_all_events
    await DB.redis.hset(user_id, 'calendar_settings', json.dumps(calendar_settings))
    await func(user_id)

    sleep_status = await DB.is_sleep(user_id)
    att_notify = await DB.redis.hget(user_id, 'att_notify')
    calendar_settings = await DB.redis.hget(user_id, 'calendar_settings')
    if not calendar_settings:
        calendar_settings = {}
        calendar_settings['diff_time'] = 5
        calendar_settings['notify'] = 0
    else:
        calendar_settings = json.loads(calendar_settings)
    if att_notify is None:
        att_notify = 1
    else:
        att_notify = int(att_notify)

    await query.message.edit_reply_markup(reply_markup=settings_btns(sleep_status, calendar_settings['notify']))
    

# @dp.throttled(trottle, rate=1)
# @Logger.log_msg
# async def att_notify(query: types.CallbackQuery, state: FSMContext):
#     user_id = query.from_user.id

#     att_notify = int(query.data.split()[1])
#     await DB.set_key(user_id, 'att_notify', att_notify)

#     sleep_status = await DB.is_sleep(user_id)
#     att_notify = int(await DB.redis.hget(user_id, 'att_notify'))
#     calendar_settings = await DB.redis.hget(user_id, 'calendar_settings')
#     if not calendar_settings:
#         calendar_settings = {}
#         calendar_settings['diff_time'] = 5
#         calendar_settings['notify'] = 0
#     else:
#         calendar_settings = json.loads(calendar_settings)
#     if att_notify is None:
#         att_notify = 1
#     else:
#         att_notify = int(att_notify)

#     await query.message.edit_reply_markup(reply_markup=settings_btns(sleep_status, calendar_settings['notify']))
     

def register_handlers_settings(dp: Dispatcher):
    dp.register_callback_query_handler(
        settings,
        lambda c: c.data == "settings",
        state="*"
    )
    dp.register_callback_query_handler(
        sleep,
        lambda c: c.data == "sleep" or c.data == "awake",
        state="*"
    )
    dp.register_callback_query_handler(
        calendar_notify,
        lambda c: c.data == "calendar_notify 1" or c.data == "calendar_notify 0",
        state="*"
    )
    # dp.register_callback_query_handler(
    #     att_notify,
    #     lambda c: c.data == "att_notify 1" or c.data == "att_notify 0",
    #     state="*"
    # )