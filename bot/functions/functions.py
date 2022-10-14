from datetime import datetime, timedelta
import json
from aiogram import types

from bot.objects import aioredis

def clear_MD(text):
    text = str(text)
    symbols = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for sym in symbols:
        text = text.replace(sym, f"\{sym}")

    return text


async def get_info_from_forwarded_msg(message: types.Message):
    user_id = None
    name = None
    mention = None

    text = ""
    if message.forward_from_chat:
        text += f"Chat id: `{clear_MD(message.forward_from_chat.id)}`\n"
    if message.forward_from:
        if message.forward_from.is_premium:
            text += "⭐️\n"
        if message.forward_from.is_bot:
            text += "BOT\n"
        user_id = message.forward_from.id
        text += f"User id: `{clear_MD(user_id)}`\n"
        if message.forward_from.full_name:
            name = message.forward_from.full_name
            text += f"Full name: `{clear_MD(name)}`\n"
        if message.forward_from.username:
            mention = message.forward_from.username
            text += f"Mention: @{clear_MD(mention)}\n"
    if message.forward_sender_name:
        text += f"Sender name: `{clear_MD(message.forward_sender_name)}`\n"
    if message.forward_from_message_id:
        text += f"Msg id: `{clear_MD(message.forward_from_message_id)}`\n"
    
    if user_id:
        if await aioredis.if_user(user_id):
            user = await aioredis.get_dict(user_id)
            if await aioredis.is_registered_moodle(user_id):
                text += f"\nBarcode: `{user['barcode']}`"
                if await aioredis.is_ready_courses(user_id):
                    try:
                        json.loads(user['courses'])
                    except:
                        text += f"\nCourses: ❌"
                    else:
                        text += f"\nCourses: ✅"
                else:
                    text += f"\nCourses: ❌"

                if await aioredis.is_ready_gpa(user_id):
                    try:
                        json.loads(user['gpa'])
                    except:
                        text += f"\nGPA: ❌"
                    else:
                        text += f"\nGPA: ✅"
                else:
                    text += f"\nGPA: ❌"
                

                if await aioredis.is_active_sub(user_id):
                    time = get_diff_time(user['end_date'])
                    text += f"\n\nSubscription is active for *{time}*"
                else:
                    text += "\n\nSubscription is *not active*"

    return text, user_id, name, mention


async def get_info_from_user_id(user_id):
    text = ""
    if user_id:
        if await aioredis.if_user(user_id):
            user = await aioredis.get_dict(user_id)
            if await aioredis.is_registered_moodle(user_id):
                text += f"\nBarcode: `{user['barcode']}`"
                if await aioredis.is_ready_courses(user_id):
                    try:
                        json.loads(user['courses'])
                    except:
                        text += f"\nCourses: ❌"
                    else:
                        text += f"\nCourses: ✅"
                else:
                    text += f"\nCourses: ❌"

                if await aioredis.is_ready_gpa(user_id):
                    try:
                        json.loads(user['gpa'])
                    except:
                        text += f"\nGPA: ❌"
                    else:
                        text += f"\nGPA: ✅"
                else:
                    text += f"\nGPA: ❌"
                

                if await aioredis.is_active_sub(user_id):
                    time = get_diff_time(user['end_date'])
                    text += f"\n\nSubscription is active for *{time}*"
                else:
                    text += "\n\nSubscription is *not active*"

    return text


async def delete_msg(*msgs):
    for msg in msgs:
        try:
            await msg.delete()
        except:
            ...


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)
    

def get_diff_time(time_str):
    due = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
    now = datetime.now()
    diff = due-now
    return chop_microseconds(diff)
