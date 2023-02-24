from datetime import datetime, timedelta
import json
import shortuuid

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import dp, rate
from modules.bot.functions.functions import clear_MD, delete_msg
from modules.bot.functions.rights import login_and_active_sub_required
from modules.bot.keyboards.moodle import confirm_delete_event, show_calendar_choices, show_calendar_day, show_calendar_day_for_edit, show_calendar_event_for_edit
from modules.scheduler import EventsScheduler

from ... import database
from ... import logger as Logger


class NewEvent(StatesGroup):
    wait_name = State()
    wait_timestart = State()
    wait_duration = State()

class EditEvent(StatesGroup):
    wait_value = State()


@dp.throttled(rate=rate)
@Logger.log_msg
@login_and_active_sub_required
async def get_calendar(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:

        await query.message.edit_text("Choose one:", reply_markup=show_calendar_choices())
    elif query.__class__ is types.Message:
        message : types.Message = query

        await message.answer("Choose one:", reply_markup=show_calendar_choices())


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def get_calendar_day(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    day_of_week = query.data.split()[1]
    text = f"*{day_of_week.capitalize()}*:\n\n"

    calendar = json.loads(await database.redis.hget(query.from_user.id, 'calendar'))
    days_events = sorted(calendar.get(day_of_week, {}).values(), key=lambda d: int(d['timestart'].replace(':', '')))

    for event in days_events:
        end_dt = datetime.now().replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1])) + timedelta(minutes=int(event['duration']))
        text += f"{clear_MD(event['name'])} \- {clear_MD(event['duration'])}min\n" \
                f"{clear_MD(event['timestart'])} \- {clear_MD(end_dt.strftime('%H:%M'))}\n\n"

    await query.message.edit_text(text, reply_markup=show_calendar_day(day_of_week), parse_mode='MarkdownV2')


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_edit_day(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    day_of_week = query.data.split()[1]

    calendar = json.loads(await database.redis.hget(query.from_user.id, 'calendar'))
    days_events = sorted(calendar.get(day_of_week, {}).values(), key=lambda d: int(d['timestart'].replace(':', '')))

    await query.message.edit_text("Choose one:", reply_markup=show_calendar_day_for_edit(day_of_week, days_events))


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_edit_event(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    _, day_of_week, _, event_uuid  = query.data.split()

    calendar = json.loads(await database.redis.hget(query.from_user.id, 'calendar'))
    event = calendar[day_of_week][event_uuid]
    end_dt = datetime.now().replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1])) + timedelta(minutes=int(event['duration']))
    text = f"{clear_MD(event['name'])} \- {clear_MD(event['duration'])}min\n" \
            f"{clear_MD(event['timestart'])} \- {clear_MD(end_dt.strftime('%H:%M'))}"

    await query.message.edit_text(text, reply_markup=show_calendar_event_for_edit(day_of_week, event_uuid), parse_mode='MarkdownV2')


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_edit_event_field(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    _, day_of_week, _, event_uuid, field  = query.data.split()

    if field == 'name':
        text = "Set new name:"
    elif field == 'timestart':
        text = "Set new time\n\nExample: 16:00:"
    elif field == 'duration':
        text = "Set new duration\n\nExample: 50:"
    await EditEvent.wait_value.set()
    
    msg = await query.message.edit_text(text)
    async with state.proxy() as data:
        data['event_day'] = day_of_week
        data['event_uuid'] = event_uuid
        data['msg_del'] = msg
        data['event_field'] = field


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_edit_event_filed_set(message: types.Message, state: FSMContext):
    if not await database.is_ready_calendar(message.from_user.id):
        await database.redis.hset(message.from_user.id, 'calendar', '{}')

    new_val = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)
        day_of_week = data['event_day']
        event_uuid = data['event_uuid']
        field = data['event_field']

    if field == 'timestart':
        if ':' not in new_val and len(new_val.split(':')) != 2 and len(new_val) != 5:
            msg = await message.answer("Error!\nWrite new time for event\n\nExample: 16:00")
            async with state.proxy() as data:
                data['msg_del'] = msg
            return
    elif field == 'duration':
        if not new_val.isdigit():
            msg = await message.answer("Error!\nWrite new duration for event\n\nExample: 50")
            async with state.proxy() as data:
                data['msg_del'] = msg
            return

    calendar = json.loads(await database.redis.hget(message.from_user.id, 'calendar'))
    calendar[day_of_week][event_uuid][field] = new_val
    await EventsScheduler.remove_event_from_scheduler(day_of_week, calendar[day_of_week][event_uuid], message.from_user.id)
    await EventsScheduler.add_new_event_to_scheduler(day_of_week, calendar[day_of_week][event_uuid], message.from_user.id)
    await database.redis.hset(message.from_user.id, 'calendar', json.dumps(calendar))

    event = calendar[day_of_week][event_uuid]
    end_dt = datetime.now().replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1])) + timedelta(minutes=int(event['duration']))
    text = f"{clear_MD(event['name'])} \- {clear_MD(event['duration'])}min\n" \
            f"{clear_MD(event['timestart'])} \- {clear_MD(end_dt.strftime('%H:%M'))}\n\n"
    msg = await message.answer(text, reply_markup=show_calendar_event_for_edit(day_of_week, event_uuid), parse_mode='MarkdownV2')
    await state.finish()


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def get_calendar_day_delete(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    _, day_of_week, _, event_uuid  = query.data.split()
    
    await query.message.edit_text("You sure?", reply_markup=confirm_delete_event(day_of_week, event_uuid))


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def get_calendar_day_delete_confirm(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    _, day_of_week, _, event_uuid, _  = query.data.split()
    calendar = json.loads(await database.redis.hget(query.from_user.id, 'calendar'))
    await EventsScheduler.remove_event_from_scheduler(day_of_week, calendar[day_of_week][event_uuid], query.from_user.id)
    del calendar[day_of_week][event_uuid]
    await database.redis.hset(query.from_user.id, 'calendar', json.dumps(calendar))
    await query.answer('Event deleted!')
    
    day_of_week = query.data.split()[1]
    text = f"*{day_of_week.capitalize()}*:\n\n"

    days_events = sorted(calendar.get(day_of_week, {}).values(), key=lambda d: int(d['timestart'].replace(':', '')))

    for event in days_events:
        end_dt = datetime.now().replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1])) + timedelta(minutes=int(event['duration']))
        text += f"{clear_MD(event['name'])} \- {clear_MD(event['duration'])}min\n" \
                f"{clear_MD(event['timestart'])} \- {clear_MD(end_dt.strftime('%H:%M'))}\n\n"

    await query.message.edit_text(text, reply_markup=show_calendar_day(day_of_week), parse_mode='MarkdownV2')
        

@dp.throttled(rate=0.5)
@Logger.log_msg
@login_and_active_sub_required
async def calendar_new_event(query: types.CallbackQuery, state: FSMContext):
    if not await database.is_ready_calendar(query.from_user.id):
        await database.redis.hset(query.from_user.id, 'calendar', '{}')

    day_of_week = query.data.split()[1]

    msg = await query.message.edit_text("Write name for new event:")
    await NewEvent.wait_name.set()
    async with state.proxy() as data:
        data['msg_del'] = msg
        data['event_day'] = day_of_week


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_new_event_name(message: types.Message, state: FSMContext):
    if not await database.is_ready_calendar(message.from_user.id):
        await database.redis.hset(message.from_user.id, 'calendar', '{}')

    name = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)

    msg = await message.answer("Write start time for new event\n\nExample: 16:00")
    await NewEvent.wait_timestart.set()
    async with state.proxy() as data:
        data['event_name'] = name
        data['msg_del'] = msg


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_new_event_time(message: types.Message, state: FSMContext):
    if not await database.is_ready_calendar(message.from_user.id):
        await database.redis.hset(message.from_user.id, 'calendar', '{}')

    time = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)

    if ':' in time and len(time.split(':')) == 2 and len(time) == 5:
        msg = await message.answer("Write duration for new event\n\nExample: 50")
        await NewEvent.wait_duration.set()
        async with state.proxy() as data:
            data['event_time'] = time
            data['msg_del'] = msg
    else:
        msg = await message.answer("Error!\nWrite start time for new event\n\nExample: 16:00")
        async with state.proxy() as data:
            data['msg_del'] = msg


@dp.throttled(rate=0.5)
@login_and_active_sub_required
async def calendar_new_event_duration(message: types.Message, state: FSMContext):
    if not await database.is_ready_calendar(message.from_user.id):
        await database.redis.hset(message.from_user.id, 'calendar', '{}')

    duration = message.text
    async with state.proxy() as data:
        await delete_msg(data['msg_del'], message)

    if duration.isdigit():
        async with state.proxy() as data:
            name = data['event_name']
            timestart = data['event_time']
            day_of_week = data['event_day']
        event_uuid = str(shortuuid.uuid())
        calendar = json.loads(await database.redis.hget(message.from_user.id, 'calendar'))
        calendar_settings = await database.redis.hget(message.from_user.id, 'calendar_settings')
        if not calendar.get(day_of_week, None):
            calendar[day_of_week] = {}
        if not calendar_settings:
            calendar_settings = {}
            calendar_settings['diff_time'] = 5
            calendar_settings['notify'] = 0
        else:
            calendar_settings = json.loads(calendar_settings)
        calendar[day_of_week][event_uuid] = {
            'name': name,
            'timestart': timestart,
            'duration': int(duration),
            'uuid': event_uuid
        }
        if calendar_settings['notify']:
            await EventsScheduler.add_new_event_to_scheduler(day_of_week, calendar[day_of_week][event_uuid], message.from_user.id, calendar_settings['diff_time'])
        await database.redis.hset(message.from_user.id, 'calendar', json.dumps(calendar))
        await database.redis.hset(message.from_user.id, 'calendar_settings', json.dumps(calendar_settings))

        msg = await message.answer("Created new event!", reply_markup=show_calendar_choices())
        await state.finish()
    else:
        msg = await message.answer("Error!\nWrite duration for new event\n\nExample: 50")
        async with state.proxy() as data:
            data['msg_del'] = msg


def register_handlers_calendar(dp: Dispatcher):
    dp.register_message_handler(get_calendar, commands="get_calendar", state="*")

    dp.register_message_handler(calendar_new_event_name, content_types=['text'], state=NewEvent.wait_name)
    dp.register_message_handler(calendar_new_event_time, content_types=['text'], state=NewEvent.wait_timestart)
    dp.register_message_handler(calendar_new_event_duration, content_types=['text'], state=NewEvent.wait_duration)

    dp.register_message_handler(calendar_edit_event_filed_set, content_types=['text'], state=EditEvent.wait_value)

    dp.register_callback_query_handler(
        get_calendar,
        lambda c: c.data == "calendar",
        state="*"
    )
    dp.register_callback_query_handler(
        get_calendar_day,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: len(c.data.split()) == 2,
        state="*"
    )
    dp.register_callback_query_handler(
        calendar_edit_day,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "edit",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )
    dp.register_callback_query_handler(
        calendar_edit_event,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "edit",
        lambda c: len(c.data.split()) == 4,
        state="*"
    )
    dp.register_callback_query_handler(
        calendar_edit_event_field,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "edit",
        lambda c: len(c.data.split()) == 5,
        state="*"
    )
    dp.register_callback_query_handler(
        get_calendar_day_delete,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "delete",
        lambda c: len(c.data.split()) == 4,
        state="*"
    )
    dp.register_callback_query_handler(
        get_calendar_day_delete_confirm,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "delete",
        lambda c: c.data.split()[4] == "confirm",
        lambda c: len(c.data.split()) == 5,
        state="*"
    )
    dp.register_callback_query_handler(
        calendar_new_event,
        lambda c: c.data.split()[0] == "calendar",
        lambda c: c.data.split()[1] in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        lambda c: c.data.split()[2] == "new_event",
        lambda c: len(c.data.split()) == 3,
        state="*"
    )