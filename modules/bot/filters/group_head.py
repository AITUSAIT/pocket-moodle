from aiogram import types
from aiogram.filters import Filter

from modules.pm_api.academic_group import AcademicGroupAPI


class IsGroupHead(Filter):
    key = "is_group_head"

    async def __call__(self, message: types.Message | types.CallbackQuery) -> bool:
        if message.from_user is None:
            return False
        if isinstance(message, types.Message):
            user_tg_id = message.from_user.id
            chat_id = message.chat.id
            return (await AcademicGroupAPI().get_academic_group_by_tg_id(chat_id)).group_head_tg_id == user_tg_id
        if isinstance(message, types.CallbackQuery):
            msg = message.message
            if msg is None:
                return False
            if isinstance(msg, types.Message):
                user_tg_id = message.from_user.id
                chat_id = msg.chat.id
                return (await AcademicGroupAPI().get_academic_group_by_tg_id(chat_id)).group_head_tg_id == user_tg_id
            if isinstance(msg, types.InaccessibleMessage):
                user_tg_id = message.from_user.id
                chat_id = msg.chat.id
                return (await AcademicGroupAPI().get_academic_group_by_tg_id(chat_id)).group_head_tg_id == user_tg_id
        return False
