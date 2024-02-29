import asyncio
import math
import re
from datetime import datetime, timedelta
from functools import wraps

from aiogram import types

import global_vars
from modules.database import DB, CourseDB, UserDB

user_timers: dict[str, asyncio.Task] = {}


async def insert_user(user_id: int):

    user = await UserDB.get_user(user_id)
    if not user:
        return

    if user in global_vars.USERS:
        global_vars.USERS.remove(user)
    global_vars.USERS.insert(0, user)


def truncate_string(input_str, max_length=15) -> str:
    if len(input_str) > max_length:
        truncated_str = input_str[: max_length - 3] + "..."
        return truncated_str
    return input_str


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[i]}"


def count_active_user(func):
    @wraps(func)
    async def wrapper(query, *args, **kwargs):
        user_id = query.from_user.id
        res = await func(query, *args, **kwargs)

        if user_id in user_timers:
            user_timers[user_id].cancel()

        async def delayed_update():
            await asyncio.sleep(15)
            async with DB.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(
                        "UPDATE users SET last_active = $1 WHERE user_id = $2;", datetime.now(), user_id
                    )
            user_timers.pop(user_id, None)

        user_timers[user_id] = asyncio.create_task(delayed_update())

        return res

    return wrapper


def clear_md(text: str | int | float) -> str:
    text = str(text)
    symbols = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]

    for sym in symbols:
        text = text.replace(sym, f"\{sym}")

    return text


async def get_info_from_forwarded_msg(message: types.Message) -> tuple[str, int | None, str | None, str | None]:
    user_id = None
    name = None
    mention = None

    text = ""
    if message.forward_from_chat:
        text += f"Chat id: `{clear_md(message.forward_from_chat.id)}`\n"
    if message.forward_from:
        if message.forward_from.is_premium:
            text += "⭐️\n"
        if message.forward_from.is_bot:
            text += "BOT\n"
        user_id = message.forward_from.id
        text += f"User id: `{clear_md(user_id)}`\n"
        if message.forward_from.full_name:
            name = message.forward_from.full_name
            text += f"Full name: `{clear_md(name)}`\n"
        if message.forward_from.username:
            mention = message.forward_from.username
            text += f"Mention: @{clear_md(mention)}\n"
    if message.forward_sender_name:
        text += f"Sender name: `{clear_md(message.forward_sender_name)}`\n"
    if message.forward_from_message_id:
        text += f"Msg id: `{clear_md(message.forward_from_message_id)}`\n"

    if user_id:
        user = await UserDB.get_user(user_id)
        if user:
            if user.has_api_token():
                text += f"\nBarcode: `{user.mail}`"
                if await CourseDB.is_ready_courses(user_id):
                    text += "\nCourses: ✅"
                else:
                    text += "\nCourses: ❌"

                if user.is_newbie():
                    text += "\nNew user: ✅"
                else:
                    text += "\nNew user: ❌"

    return text, user_id, name, mention


async def get_info_from_user_id(user_id: str) -> str:
    text = f"User ID: `{user_id}\n`"
    if user_id:
        user = await UserDB.get_user(user_id)
        if user:
            if user.has_api_token():
                text += f"\nMail: `{user.mail}`"
                if await CourseDB.is_ready_courses(user_id):
                    text += "\nCourses: ✅"
                else:
                    text += "\nCourses: ❌"

                if user.is_newbie():
                    text += "\nNew user: ✅"
                else:
                    text += "\nNew user: ❌"

    return text


async def delete_msg(*msgs: types.Message):
    for msg in reversed(msgs):
        try:
            await msg.delete()
        except Exception:
            ...


def chop_microseconds(delta: timedelta) -> timedelta:
    return delta - timedelta(microseconds=delta.microseconds)


def get_diff_time(time) -> timedelta:
    if isinstance(time, str):
        try:
            due = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
        except Exception:
            due = datetime.strptime(time, "%A, %d %B %Y, %I:%M %p")
    else:
        due = time

    now = datetime.now()
    diff = due - now
    return chop_microseconds(diff)


def check_is_valid_mail(mail):
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    return re.match(regex, mail) is not None
