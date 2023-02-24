from functools import wraps

from aiogram import types
from aiogram.dispatcher.filters import Filter

from modules.bot.keyboards.default import main_menu

from ... import database

admin_list = [626591599]


def is_Admin(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message: types.Message = args[0]
        if message.from_user.id in admin_list:
            return await func(*args, **kwargs)
    return wrapper


def is_admin(user_id: int):
    return True if user_id in admin_list else False


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):
        return message.from_user.id in admin_list


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):
        if await database.if_user(message.from_user.id):
            return await database.is_active_sub(message.from_user.id)
        return False


def login_and_active_sub_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg = args[0]
        user_id = arg.from_user.id
        if arg.__class__ is types.Message:
            arg: types.Message
            if not await database.if_user(user_id):
                await arg.reply("First you need to /register_moodle", reply_markup=main_menu())
            elif not await database.is_registered_moodle(user_id):
                await arg.reply("First you need to /register_moodle", reply_markup=main_menu())
            elif not await database.is_active_sub(user_id):
                await arg.reply("Your subscription is not active. /purchase", reply_markup=main_menu())
            else:
                return await func(*args, **kwargs)
            return
        elif arg.__class__ is types.CallbackQuery:
            arg: types.CallbackQuery
            if not await database.if_user(user_id):
                await arg.answer("First you need to /register_moodle")
            elif not await database.is_registered_moodle(user_id):
                await arg.answer("First you need to /register_moodle")
            elif not await database.is_active_sub(user_id):
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
        if arg.__class__ is types.Message:
            arg: types.Message
            if not await database.if_user(user_id):
                await arg.reply("First you need to /register_moodle", reply_markup=main_menu())
            elif not await database.is_registered_moodle(user_id):
                await arg.reply("First you need to /register_moodle", reply_markup=main_menu())
            else:
                return await func(*args, **kwargs)
            return
        elif arg.__class__ is types.CallbackQuery:
            arg: types.CallbackQuery
            if not await database.if_user(user_id):
                await arg.answer("First you need to /register_moodle")
            elif not await database.is_registered_moodle(user_id):
                await arg.answer("First you need to /register_moodle")
            else:
                return await func(*args, **kwargs)
            return 
    return wrapper


def active_sub_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg = args[0]
        user_id = arg.from_user.id
        if arg.__class__ is types.Message:
            arg: types.Message
            if not await database.is_active_sub(user_id):
                await arg.reply("Your subscription is not active. /purchase", reply_markup=main_menu())
            else:
                return await func(*args, **kwargs)
            return
        elif arg.__class__ is types.CallbackQuery:
            arg: types.CallbackQuery
            if not await database.is_active_sub(user_id):
                await arg.answer("Your subscription is not active. /purchase")
            else:
                return await func(*args, **kwargs)
            return 
    return wrapper
