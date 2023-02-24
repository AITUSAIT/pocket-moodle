import json
from datetime import datetime

import aioredis
from aioredis.client import Redis
from dateutil.relativedelta import relativedelta


def clear_MD(text: str) -> str:
    text = str(text)
    symbols = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for sym in symbols:
        text = text.replace(sym, f"\{sym}")

    return text


redis: Redis = None
redis1: Redis = None


async def start_redis(user: str, passwd: str, host: str, port: str, db: str):
    global redis
    redis = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/{db}", decode_responses=True)
    global redis1
    redis1 = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/1", decode_responses=True)


async def set_key(name: str, key: str, value):
    await redis.hset(name, key, value)


async def get_key(name: str, key: str):
    return await redis.hget(name, key)


async def set_keys(name: str, dict: dict):
    await redis.hmset(name, dict)


async def get_keys(name: str, *keys) -> tuple:
    return await redis.hmget(name, *keys)


async def get_dict(name: str) -> dict:
    return await redis.hgetall(name)


async def if_user(user_id: int) -> bool:
    if await redis.exists(user_id) == 0:
        return False
    else:
        return True


async def is_registered_moodle(user_id: int) -> bool:
    if await redis.hget(user_id, 'barcode'):
        return True
    else:
        return False


async def new_user(user_id: int):
    new_user = {
        'user_id': user_id,
        'ignore': 1,
        'register_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    }

    await set_keys(user_id, new_user)


async def activate_subs(user_id: int, days: int):
    user = {}
    if await is_active_sub(user_id):
        date_str = await get_key(user_id, 'end_date')
        user['end_date'] = str(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') + relativedelta(days=days))
    else:
        user['end_date'] = str(datetime.now() + relativedelta(days=days))
    user['message_end_date'] = 0

    await set_keys(user_id, user)


async def is_new_user(user_id: int) -> bool:
    if not await if_user(user_id):
        return False

    date_str = await get_key(user_id, 'register_date')

    if date_str is None:
        return False

    if datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') > datetime.now() - relativedelta(days=7):
        return True
    else:
        return False


async def is_active_sub(user_id: int) -> bool:
    if not await if_user(user_id):
        return False

    date_str = await get_key(user_id, 'end_date')

    if date_str is None:
        return False

    if datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
        return True
    else:
        return False


async def is_ready_courses(user_id: int) -> bool:
    if await if_user(user_id):
        if await redis.hexists(user_id, 'courses') == 1:
            return True
        else:
            return False
    else:
        return False


async def is_ready_calendar(user_id: int) -> bool:
    if await if_user(user_id):
        if await redis.hexists(user_id, 'calendar') == 1:
            return True
        else:
            return False
    else:
        return False


async def is_ready_curriculum(user_id: int) -> bool:
    if await if_user(user_id):
        if await redis.hexists(user_id, 'curriculum') == 1:
            return True
        else:
            return False
    else:
        return False


async def is_ready_gpa(user_id: int) -> bool:
    if await if_user(user_id):
        if await redis.hexists(user_id, 'gpa') == 1:
            return True
        else:
            return False
    else:
        return False


async def is_sleep(user_id: int) -> bool:
    if await if_user(user_id):
        if await redis.hexists(user_id, 'sleep') == 1:
            if int(await redis.hget(user_id, 'sleep')) == 1:
                return True
            else:
                return False
        else:
            return False
    else:
        return False


async def get_gpa_text(user_id: int) -> str:
    gpa_dict = json.loads(await redis.hget(user_id, 'gpa'))
    
    text = 'Your *GPA*:\n\n'
    for key in gpa_dict:
        text += f"{clear_MD(key)} \- *{clear_MD(gpa_dict[key])}*\n"
    
    return text


async def user_register_moodle(user_id: int, barcode: str, passwd: str):
    user = {}
    user['barcode'] = barcode
    user['passwd'] = crypt(passwd, barcode)
    user['sleep'] = 0
    user['message'] = 0
    user['ignore'] = 1

    await redis.hdel(user_id, 'att_statistic', 'gpa', 'courses', 'cookies', 'token', 'message', 'message_end_date')
    await set_keys(user_id, user)


async def check_if_msg_end_date(user_id: int) -> int:
    if not await redis.hexists(user_id, 'message_end_date'):
        return False

    message = int(await redis.hget(user_id, 'message_end_date'))
    return message


async def set_msg_end_date(user_id: int, number: int):
    await redis.hset(user_id, 'message_end_date', number)


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
