from aiogram import types
from aiogram.filters import Filter
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
        return await UserDB.if_admin(message.from_user.id) or await UserDB.if_manager(message.from_user.id)


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
