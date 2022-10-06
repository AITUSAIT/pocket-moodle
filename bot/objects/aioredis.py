from datetime import datetime
import json

from dateutil.relativedelta import relativedelta

import aioredis

from config import bot
from bot.functions.functions import clear_MD

redis : aioredis.Redis = None


async def start_redis(user, passwd, host, port, db):
    global redis
    redis = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/{db}", decode_responses=True)


async def start_redis1(user, passwd, host, port, db):
    global redis1
    redis1 = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/{db}", decode_responses=True)


async def set_key(key, key2, value):
    global redis
    await redis.hset(key, key2, value)


async def get_key(dict_key, key):
    global redis
    return await redis.hget(dict_key, key)


async def set_keys(key, dict):
    global redis
    await redis.hmset(key, dict)


async def get_keys(dict_key, *keys):
    global redis
    return await redis.hmget(dict_key, *keys)


async def get_dict(key):
    global redis
    return await redis.hgetall(key)


async def if_user(user_id):
    global redis
    if await redis.exists(user_id) == 0:
        return False
    else:
        return True


async def is_activaited_demo(user_id):
    global redis
    if int(await redis.hget(user_id, 'demo')) == 1:
        return True
    else:
        return False


async def is_registered_moodle(user_id):
    global redis
    if await redis.hget(user_id, 'barcode'):
        return True
    else:
        return False


async def new_user(user_id):
    new_user = {
        'user_id': user_id,
        'demo': 0,
        'ignore': 1
    }

    await set_keys(user_id, new_user)


async def activate_subs(user_id, days):
    user = {}
    if await is_active_sub(user_id):
        date_str = await get_key(user_id, 'end_date')
        user['end_date'] = str(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') + relativedelta(days=days))
    else:
        user['end_date'] = str(datetime.now() + relativedelta(days=days))

    await set_keys(user_id, user)


async def is_active_sub(user_id):
    if not await if_user(user_id):
        return False

    date_str = await get_key(user_id, 'end_date')

    if date_str is None:
        return False

    if datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
        return True
    else:
        return False


async def is_ready_courses(user_id):
    if await if_user(user_id):
        if await redis.hexists(user_id, 'courses') == 1:
            return True
        else:
            return False
    else:
        return False


async def is_ready_gpa(user_id):
    if await if_user(user_id):
        if await redis.hexists(user_id, 'gpa') == 1:
            return True
        else:
            return False
    else:
        return False


async def get_gpa_text(user_id):
    gpa_dict = json.loads(await redis.hget(user_id, 'gpa'))
    
    text = ''
    for key in gpa_dict:
        text += f"*{clear_MD(key)}* \- {clear_MD(gpa_dict[key])}\n"
    
    return text


async def user_register_moodle(user_id, barcode, passwd):
    user = {}
    user['barcode'] = barcode
    user['passwd'] = crypt(passwd, barcode)
    user['grades_sub'] = 1
    user['deadlines_sub'] = 1
    user['message'] = 0

    await set_keys(user_id, user)


async def get_mailing_sub(user_id):
    global redis
    sub_grades = int(await redis.hget(user_id, 'grades_sub'))
    sub_deadlines = int(await redis.hget(user_id, 'deadlines_sub'))

    return sub_grades, sub_deadlines


async def sub_on_mailing(user_id, mailing_type, mailing_bool):
    user = {}
    user[mailing_type] = mailing_bool

    await set_keys(user_id, user)


async def close():
    await redis.close()


def crypto(message: str, secret: str) -> str:
    new_chars = list()
    i = 0
    for num_chr in (ord(c) for c in message):
        num_chr ^= ord(secret[i])
        new_chars.append(num_chr)
        i += 1
        if i >= len(secret):
            i = 0
    return ''.join(chr(c) for c in new_chars)


def crypt(message: str, secret: str) -> str:
    return crypto(message, secret).encode('utf-8').hex()


def decrypt(message_hex: str, secret: str) -> str:
    message = bytes.fromhex(message_hex).decode('utf-8')
    return crypto(message, secret)
