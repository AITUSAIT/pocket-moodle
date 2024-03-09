from functools import wraps

from aiogram import types
from aiogram.dispatcher.filters import Filter

from modules.bot.keyboards.default import main_menu
from modules.database import UserDB


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        return await UserDB.if_admin(message.from_user.id)


class IsManager(Filter):
    key = "is_manager"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        return await UserDB.if_manager(message.from_user.id)


class IsNotStuff(Filter):
    key = "is_not_stuff"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        return not await UserDB.if_manager(message.from_user.id) and not await UserDB.if_admin(message.from_user.id)


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        user = await UserDB.get_user(message.from_user.id)
        if user:
            return True
        return False


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg: types.CallbackQuery | types.Message = args[0]
        user_id = arg.from_user.id
        user = await UserDB.get_user(user_id)

        if isinstance(arg, types.Message):
            msg: types.Message = arg
            if not user or not user.has_api_token():
                await msg.reply("First you need to /register", reply_markup=main_menu())
                return

            await func(*args, **kwargs)
        elif isinstance(arg, types.CallbackQuery):
            query: types.CallbackQuery = arg
            if not user or not user.has_api_token():
                await query.answer("First you need to /register")
                return

            await func(*args, **kwargs)

    return wrapper
