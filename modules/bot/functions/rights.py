from functools import wraps

from aiogram import types
from aiogram.dispatcher.filters import Filter

from ...bot.keyboards.default import main_menu
from ...database import UserDB
from ...database.models import User


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):
        return await UserDB.if_admin(message.from_user.id)


class IsManager(Filter):
    key = "is_manager"

    async def check(self, message: types.Message):
        return await UserDB.if_manager(message.from_user.id)


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):
        user: User = await UserDB.get_user(message.from_user.id)
        if user:
            return user.is_active_sub()
        return False


def login_and_active_sub_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg = args[0]
        user_id = arg.from_user.id
        user: User = await UserDB.get_user(user_id)

        if arg.__class__ is types.Message:
            arg: types.Message
            if not user or not user.has_api_token():
                await arg.reply("First you need to /register", reply_markup=main_menu())
            elif not user.is_active_sub():
                await arg.reply("Your subscription is not active. /purchase", reply_markup=main_menu())
            else:
                return await func(*args, **kwargs)
            return
        elif arg.__class__ is types.CallbackQuery:
            arg: types.CallbackQuery
            if not user or not user.has_api_token():
                await arg.answer("First you need to /register")
            elif not user.is_active_sub():
                await arg.answer("Your subscription is not active. /purchase")
            else:
                return await func(*args, **kwargs)
            return 
    return wrapper


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg = args[0]
        user_id = arg.from_user.id
        user: User = await UserDB.get_user(user_id)

        if arg.__class__ is types.Message:
            arg: types.Message
            if not user or not user.has_api_token():
                await arg.reply("First you need to /register", reply_markup=main_menu())
            else:
                return await func(*args, **kwargs)
            return
        elif arg.__class__ is types.CallbackQuery:
            arg: types.CallbackQuery
            if not user or not user.has_api_token():
                await arg.answer("First you need to /register")
            else:
                return await func(*args, **kwargs)
            return 
    return wrapper
