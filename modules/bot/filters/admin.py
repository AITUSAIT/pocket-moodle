from aiogram import types
from aiogram.filters import Filter

from modules.pm_api.api import PocketMoodleAPI


class IsAdmin(Filter):
    key = "is_admin"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False
        user = await PocketMoodleAPI().get_user(message.from_user.id)
        return user.is_admin if user else False


class IsManager(Filter):
    key = "is_manager"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False
        user = await PocketMoodleAPI().get_user(message.from_user.id)
        return (user.is_admin or user.is_manager) if user else False


class IsNotStuff(Filter):
    key = "is_not_stuff"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        if message.from_user is None:
            return True
        user = await PocketMoodleAPI().get_user(message.from_user.id)
        return (not user.is_admin and not user.is_manager) if user else True


class IsUser(Filter):
    key = "is_user"

    async def check(self, message: types.Message):  # pylint: disable=arguments-differ
        if message.from_user is None:
            return False

        user = await PocketMoodleAPI().get_user(message.from_user.id)
        if user:
            return True
        return False
