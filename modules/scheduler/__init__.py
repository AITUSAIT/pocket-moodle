import asyncio
from datetime import datetime, timedelta
import json
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import ConflictingIdError

from ..logger import logger
from config import bot

from .. import database

days = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

async def send_msg(user_id: str, event: dict):
    calendar_settings = await database.redis.hget(user_id, 'calendar_settings')
    if not calendar_settings:
        calendar_settings = {}
        calendar_settings['diff_time'] = 5
        calendar_settings['notify'] = 0
    else:
        calendar_settings = json.loads(calendar_settings)

    if calendar_settings['notify']:
        now = datetime.now()
        dt = now.replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1]))
        diff = chop_microseconds(dt-now)
        text = "Event upcoming:\n\n" \
                f"{event['name']} \- {event['duration']}min\n" \
                f"{event['timestart']}\n" \
                f"Remaining: {diff}"

        await bot.send_message(user_id, text, parse_mode='MarkdownV2')

class EventsScheduler:
    jobstores = {
        'sqlite': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty", jobstores=jobstores)

    async def add_new_event_to_scheduler(day_of_week: str, event: dict, user_id: str, diff_min:int | None = None):
        if diff_min is None:
            diff_min = 5

        dt = datetime.now().replace(hour=int(event['timestart'].split(':')[0]), minute=int(event['timestart'].split(':')[1]))
        diff_dt = dt - timedelta(minutes=diff_min)

        EventsScheduler.scheduler.add_job(
            send_msg, 'cron', [user_id, event],
            day_of_week=days[day_of_week],
            hour=diff_dt.hour,
            minute=diff_dt.minute, 
            id=f"{user_id}_{day_of_week}_{event['uuid']}",
            jobstore='sqlite'
        )

    async def remove_event_from_scheduler(day_of_week: str, event: dict, user_id: str):
        try:
            EventsScheduler.scheduler.remove_job(f"{user_id}_{day_of_week}_{event['uuid']}", jobstore='sqlite')
        except Exception as exc:
            print(exc)
            ...

    async def get_calendar_and_add_events(user_id: str):
        user = await database.get_dict(user_id)
        calendar = user.get('calendar', None)
        calendar_settings = user.get('calendar_settings', None)
        if calendar is None:
            return

        if calendar_settings is None:
            calendar_settings = {}
            calendar_settings['diff_time'] = 5
            calendar_settings['notify'] = 0
        else:
            calendar_settings = json.loads(calendar_settings)

        if not calendar_settings['notify']:
            return

        calendar: dict = json.loads(calendar)
        for day_of_week, events in calendar.items():
            for event in events.values(): 
                await EventsScheduler.add_new_event_to_scheduler(day_of_week, event, user_id, calendar_settings['diff_time'])

    async def load_events():
        users_ids: list = await database.redis.keys()
        if 'news' in users_ids:
            users_ids.remove('news')

        await asyncio.gather(*[EventsScheduler.get_calendar_and_add_events(user_id) for user_id in users_ids])
        logger.info(f"Events loaded!")

    async def delete_all_events(user_id: str):
        user = await database.get_dict(user_id)
        calendar = user.get('calendar', None)
        if calendar is None:
            return

        calendar: dict = json.loads(calendar)
        for day_of_week, events in calendar.items():
            for event in events.values(): 
                await EventsScheduler.remove_event_from_scheduler(day_of_week, event, user_id)

    async def start_scheduler():
        # os.remove('jobs.sqlite')
        await EventsScheduler.load_events()
        EventsScheduler.scheduler.start()
