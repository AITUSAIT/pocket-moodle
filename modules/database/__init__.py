import json
from datetime import datetime

from redis import asyncio as aioredis
from redis.asyncio.client import Redis
from dateutil.relativedelta import relativedelta


def clear_MD(text: str) -> str:
    text = str(text)
    symbols = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for sym in symbols:
        text = text.replace(sym, f"\{sym}")

    return text


class DB:
    redis: Redis
    redis1: Redis

    @classmethod
    async def start_redis(cls, user: str, passwd: str, host: str, port: str, db: str):
        cls.redis = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/{db}", decode_responses=True)
        cls.redis1 = await aioredis.from_url(f"redis://{user}:{passwd}@{host}:{port}/1", decode_responses=True)

    @classmethod
    async def set_key(cls, name: str, key: str, value):
        await cls.redis.hset(name, key, value)

    @classmethod
    async def get_key(cls, name: str, key: str):
        return await cls.redis.hget(name, key)

    @classmethod
    async def set_keys(cls, name: str, dict: dict):
        await cls.redis.hmset(name, dict)

    @classmethod
    async def get_keys(cls, name: str, *keys) -> tuple:
        return await cls.redis.hmget(name, *keys)

    @classmethod
    async def get_dict(cls, name: str) -> dict:
        return await cls.redis.hgetall(name)

    @classmethod
    async def if_user(cls, user_id: int) -> bool:
        if await cls.redis.exists(user_id) == 0:
            return False
        else:
            return True
        
    @classmethod
    async def if_admin(cls, user_id: int) -> bool:
        admins = await cls.redis1.hgetall('admins')

        return str(user_id) in admins
    
    @classmethod
    async def if_manager(cls, user_id: int) -> bool:
        managers = await cls.redis1.hgetall('managers')

        return str(user_id) in managers or await cls.if_admin(user_id)

    @classmethod
    async def is_registered_moodle(cls, user_id: int) -> bool:
        if await cls.redis.hget(user_id, 'barcode'):
            return True
        else:
            return False

    @classmethod
    async def new_user(cls, user_id: int):
        new_user = {
            'user_id': user_id,
            'ignore': 1,
            'register_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        }

        await cls.set_keys(user_id, new_user)

    @classmethod
    async def activate_subs(cls, user_id: int, days: int):
        user = {}
        user['message_end_date'] = 0
        if await cls.is_active_sub(user_id):
            date_str = await cls.get_key(user_id, 'end_date')
            user['end_date'] = str(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') + relativedelta(days=days))
        else:
            user['end_date'] = str(datetime.now() + relativedelta(days=days))
        user['message_end_date'] = 0

        await cls.set_keys(user_id, user)

    @classmethod
    async def is_new_user(cls, user_id: int) -> bool:
        if not await cls.if_user(user_id):
            return False

        date_str = await cls.get_key(user_id, 'register_date')

        if date_str is None:
            return False

        if datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') > datetime.now() - relativedelta(days=7):
            return True
        else:
            return False

    @classmethod
    async def is_active_sub(cls, user_id: int) -> bool:
        if not await cls.if_user(user_id):
            return False

        date_str = await cls.get_key(user_id, 'end_date')

        if date_str is None:
            return False

        if datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
            return True
        else:
            return False

    @classmethod
    async def is_ready_courses(cls, user_id: int) -> bool:
        if await cls.if_user(user_id):
            if await cls.redis.hexists(user_id, 'courses') == 1:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    async def is_ready_calendar(cls, user_id: int) -> bool:
        if await cls.if_user(user_id):
            if await cls.redis.hexists(user_id, 'calendar') == 1:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    async def is_ready_curriculum(cls, user_id: int) -> bool:
        if await cls.if_user(user_id):
            if await cls.redis.hexists(user_id, 'curriculum') == 1:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    async def is_ready_gpa(cls, user_id: int) -> bool:
        if await cls.if_user(user_id):
            if await cls.redis.hexists(user_id, 'gpa') == 1:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    async def is_sleep(cls, user_id: int) -> bool:
        if await cls.if_user(user_id):
            if await cls.redis.hexists(user_id, 'sleep') == 1:
                if int(await cls.redis.hget(user_id, 'sleep')) == 1:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    @classmethod
    async def get_gpa_text(cls, user_id: int) -> str:
        gpa_dict = json.loads(await cls.redis.hget(user_id, 'gpa'))
        
        text = 'Your *GPA*:\n\n'
        for key in gpa_dict:
            text += f"{clear_MD(key)} \- *{clear_MD(gpa_dict[key])}*\n"
        
        return text

    @classmethod
    async def user_register_moodle(cls, user_id: int, barcode: str, passwd: str):
        user = {}
        user['barcode'] = barcode
        user['passwd'] = cls.crypt(passwd, barcode)
        user['sleep'] = 0
        user['message'] = 0
        user['ignore'] = 1

        await cls.redis.hdel(user_id, 'att_statistic', 'gpa', 'courses', 'cookies', 'token', 'message', 'message_end_date')
        await cls.set_keys(user_id, user)

    @classmethod
    async def check_if_msg_end_date(cls, user_id: int) -> bool:
        if not await cls.redis.hexists(user_id, 'message_end_date'):
            return False

        return bool(await cls.redis.hget(user_id, 'message_end_date'))

    @classmethod
    async def set_msg_end_date(cls, user_id: int, number: int):
        await cls.redis.hset(user_id, 'message_end_date', number)

    @classmethod
    async def get_email(cls, user_id: int) -> int:
        if not await cls.redis.hexists(user_id, 'email'):
            return None

        return await cls.redis.hget(user_id, 'email')

    @classmethod
    async def save_new_payment(cls, transaction):
        await cls.redis1.hset('payments', transaction['trackId'], json.dumps(transaction))

    @classmethod
    async def get_payment(cls, id):
        return json.loads(await cls.redis1.hget('payments', id))

    @classmethod
    async def close(cls):
        await cls.redis.close()


    @classmethod
    def crypto(cls, message: str, secret: str) -> str:
        new_chars = list()
        i = 0
        for num_chr in (ord(c) for c in message):
            num_chr ^= ord(secret[i])
            new_chars.append(num_chr)
            i += 1
            if i >= len(secret):
                i = 0
        return ''.join(chr(c) for c in new_chars)


    @classmethod
    def crypt(cls, message: str, secret: str) -> str:
        return cls.crypto(message, secret).encode('utf-8').hex()


    @classmethod
    def decrypt(cls, message_hex: str, secret: str) -> str:
        message = bytes.fromhex(message_hex).decode('utf-8')
        return cls.crypto(message, secret)
