from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: list):
        self.chat_type = chat_type

    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, Message):
            return message.chat.type in self.chat_type
        if isinstance(message, CallbackQuery):
            query = message
            if not query.message:
                return False

            return query.message.chat.type in self.chat_type