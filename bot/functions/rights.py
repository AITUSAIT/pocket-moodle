from functools import wraps

from aiogram import types
from aiogram.dispatcher.filters import Filter
from aiogram import types
from bot.objects import aioredis


admin_list = [626591599]


def is_Admin(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message: types.Message = args[0]
        if message.from_user.id in admin_list:
            return await func(*args, **kwargs)
    return wrapper


def is_admin(user_id):
    return True if user_id in admin_list else False


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):
        return message.from_user.id in admin_list


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):
        if await aioredis.if_user(message.from_user.id):
            return await aioredis.is_active_sub(message.from_user.id)
        return False