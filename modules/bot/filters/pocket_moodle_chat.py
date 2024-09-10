from aiogram import types
from aiogram.filters import Filter


class IsPocketMoodleChat(Filter):
    key = "is_pocket_moodle_chat"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        return message.chat.id == -1001768548002


class IsNotPocketMoodleChat(Filter):
    key = "is_pocket_moodle_chat"

    async def __call__(self, message: types.Message) -> bool:  # pylint: disable=arguments-differ
        return message.chat.id != -1001768548002
