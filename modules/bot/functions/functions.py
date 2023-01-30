import json
import random
import string
from datetime import datetime, timedelta
from typing import BinaryIO

import aiohttp
from aiogram import types

from ... import database


def clear_MD(text: str) -> str:
    text = str(text)
    symbols = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for sym in symbols:
        text = text.replace(sym, f"\{sym}")

    return text


async def generate_promocode():
    len = 10
    while 1:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k = len)) 
        if not await database.redis1.hexists('promocodes', code):
            return code


async def upload_file(file: BinaryIO, file_name: str, token: str):
    data = aiohttp.FormData()
    data.add_field('filecontent', file, filename=file_name, content_type='multipart/form-data')

    args = {
        'moodlewsrestformat': 'json',
        'wstoken': token,
        'token': token,
        'wsfunction': 'core_files_upload',
        'filearea': 'draft',
        'itemid': 0,
        'filepath': '/'
    }

    async with aiohttp.ClientSession('https://moodle.astanait.edu.kz') as session:
            async with session.post("/webservice/upload.php", params=args, data=data) as res:
                response = json.loads(await res.text())
                return response


async def save_submission(token: str, assign_id: str, item_id:str = '', text: str = ''):
    args = {
        'moodlewsrestformat': 'json',
        'wstoken': token,
        'wsfunction': 'mod_assign_save_submission',
        'assignmentid': assign_id
    }
    if item_id != '':
        args['plugindata[files_filemanager]'] = item_id
    if text != '':
        args['plugindata[onlinetext_editor][itemid]'] = 0
        args['plugindata[onlinetext_editor][format]'] = 0
        args['plugindata[onlinetext_editor][text]'] = text

    async with aiohttp.ClientSession('https://moodle.astanait.edu.kz') as session:
            async with session.post("/webservice/rest/server.php", params=args) as res:
                response = json.loads(await res.text())
                return response


async def get_info_from_forwarded_msg(message: types.Message) -> tuple[str, int, str, str]:
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
        if await database.if_user(user_id):
            user = await database.get_dict(user_id)
            if await database.is_registered_moodle(user_id):
                text += f"\nBarcode: `{user['barcode']}`"
                if await database.is_ready_courses(user_id):
                    try:
                        json.loads(user['courses'])
                    except:
                        text += f"\nCourses: ❌"
                    else:
                        text += f"\nCourses: ✅"
                else:
                    text += f"\nCourses: ❌"

                if await database.is_ready_gpa(user_id):
                    try:
                        json.loads(user['gpa'])
                    except:
                        text += f"\nGPA: ❌"
                    else:
                        text += f"\nGPA: ✅"
                else:
                    text += f"\nGPA: ❌"
                

                if await database.is_active_sub(user_id):
                    time = get_diff_time(user['end_date'])
                    text += f"\n\nSubscription is active for *{time}*"
                else:
                    text += "\n\nSubscription is *not active*"

    return text, user_id, name, mention


async def get_info_from_user_id(user_id: str) -> str:
    text = f"User ID: `{user_id}\n`"
    if user_id:
        if await database.if_user(user_id):
            user = await database.get_dict(user_id)
            if await database.is_registered_moodle(user_id):
                text += f"Barcode: `{user['barcode']}`"
                if await database.is_ready_courses(user_id):
                    try:
                        json.loads(user['courses'])
                    except:
                        text += f"\nCourses: ❌"
                    else:
                        text += f"\nCourses: ✅"
                else:
                    text += f"\nCourses: ❌"

                if await database.is_ready_gpa(user_id):
                    try:
                        json.loads(user['gpa'])
                    except:
                        text += f"\nGPA: ❌"
                    else:
                        text += f"\nGPA: ✅"
                else:
                    text += f"\nGPA: ❌"
                

                if await database.is_active_sub(user_id):
                    time = get_diff_time(user['end_date'])
                    text += f"\n\nSubscription is active for *{time}*"
                else:
                    text += "\n\nSubscription is *not active*"

    return text


async def delete_msg(*msgs: types.Message):
    msgs = reversed(msgs)    
    for msg in msgs:
        try:
            await msg.delete()
        except:
            ...


def chop_microseconds(delta: timedelta) -> timedelta:
    return delta - timedelta(microseconds=delta.microseconds)
    

def get_diff_time(time_str: str) -> timedelta:
    try:
        due = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
    except:
        due = datetime.strptime(time_str, '%A, %d %B %Y, %I:%M %p')
    now = datetime.now()
    diff = due-now
    return chop_microseconds(diff)
