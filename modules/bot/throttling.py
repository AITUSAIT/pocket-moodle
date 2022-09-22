import time
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InaccessibleMessage, Message


def rate_limit(limit: float) -> Callable[..., Any]:
    def decorator(func) -> Any:
        setattr(func, "throttling_rate_limit", limit)
        if func.__qualname__:
            setattr(func, "throttling_key", func.__qualname__)
        return func

    return decorator


class ThrottleManager:
    def __init__(self) -> None:
        self.throttles: dict[str, Any] = {}

    def is_throttled(self, key: str, rate: float) -> bool:
        current_time = time.time()
        last_call_time = self.throttles.get(key, 0)
        if current_time - last_call_time < rate:
            return True
        self.throttles[key] = current_time
        return False


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.5, key_prefix="antiflood_") -> None:
        self.rate_limit = limit
        self.prefix = key_prefix
        self.throttle_manager = ThrottleManager()
        super().__init__()

    async def __call__(self, handler: Callable, event: Message | CallbackQuery, data) -> None:  # type: ignore
        limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
        key_suffix = ""
        if isinstance(event, CallbackQuery):
            if not event.message:
                return
            if isinstance(event.message, InaccessibleMessage):
                return
            key_suffix = getattr(handler, "throttling_key", f"{event.from_user.id}_{event.message.chat.id}")
        elif isinstance(event, Message):
            if not event.from_user:
                return
            key_suffix = getattr(handler, "throttling_key", f"{event.from_user.id}_{event.chat.id}")
        key = f"{self.prefix}{key_suffix}"

        if self.throttle_manager.is_throttled(key, limit):
            return await self.__reply(event=event, text="You're doing that too often. Please wait a bit.")

        await handler(event, data)

    async def __reply(self, event: Message | CallbackQuery, text: str) -> None:
        if isinstance(event, CallbackQuery):
            await event.answer(text)
        elif isinstance(event, Message):
            await event.reply(text)
