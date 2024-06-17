from functools import wraps

from aiogram import types
from aiogram.filters import Filter

from modules.bot.keyboards.default import main_menu
from modules.database import UserDB


class IsAdmin(Filter):
    key = "is_admin"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False
        return await UserDB.if_admin(message.from_user.id)


class IsManager(Filter):
    key = "is_manager"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False
        return await UserDB.if_manager(message.from_user.id)


class IsNotStuff(Filter):
    key = "is_not_stuff"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return True
        return not await UserDB.if_manager(message.from_user.id) and not await UserDB.if_admin(message.from_user.id)


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False

        user = await UserDB.get_user(message.from_user.id)
        if user:
            return True
        return False


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg: types.CallbackQuery | types.Message = args[0]
        if not arg.from_user:
            return

        user_id = arg.from_user.id
        user = await UserDB.get_user(user_id)

        if isinstance(arg, types.Message):
            msg: types.Message = arg
            if not user or not user.has_api_token():
                await msg.reply("First you need to /register", reply_markup=main_menu().as_markup())
                return

            await func(*args, **kwargs)
        elif isinstance(arg, types.CallbackQuery):
            query: types.CallbackQuery = arg
            if not user or not user.has_api_token():
                await query.answer("First you need to /register")
                return

            await func(*args, **kwargs)

    return wrapper
