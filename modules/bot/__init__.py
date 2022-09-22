from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)

from config import RATE, TEST
from modules.bot.filters.admin import IsNotStuff
from modules.bot.filters.chat_type import ChatTypeFilter
from modules.bot.handlers.errors import register_handlers_errors

from .handlers.admin import ignore, register_handlers_admin
from .handlers.course_contents import register_handlers_courses_contents
from .handlers.default import register_handlers_default
from .handlers.group import register_handlers_groups
from .handlers.moodle import register_handlers_moodle
from .handlers.settings import register_handlers_settings
from .throttling import ThrottlingMiddleware


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),
        BotCommand(command="/check_finals", description="Check Finals"),
        BotCommand(command="/register", description="Register account"),
        BotCommand(command="/update", description="Update info"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())

    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),
        BotCommand(command="/check_finals", description="Check Finals"),
        BotCommand(command="/register", description="Register account"),
        BotCommand(command="/update", description="Update info"),
        BotCommand(command="/send_msg", description="(Admin)"),
        BotCommand(command="/get", description="(Admin)"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeChat(chat_id=626591599))

    commands = [
        BotCommand(command="/get_deadlines", description="Get deadlines (Group)"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeAllGroupChats())

    commands = [
        BotCommand(command="/start", description="Register group"),
        BotCommand(command="/get_deadlines", description="Get deadlines (Group)"),
        BotCommand(command="/stop", description="Unregister group"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeAllChatAdministrators())


async def register_bot_handlers(bot: Bot, dp: Dispatcher):
    dp.message.middleware(ThrottlingMiddleware(limit=RATE, key_prefix="antiflood"))
    dp.callback_query.middleware(ThrottlingMiddleware(limit=RATE, key_prefix="antiflood"))

    group_chats_router = Router()
    group_chats_router.message.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))
    group_chats_router.callback_query.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))
    register_handlers_groups(group_chats_router)

    personal_chats_router = Router()
    personal_chats_router.message.filter(ChatTypeFilter(chat_type=["sender", "private"]))
    personal_chats_router.callback_query.filter(ChatTypeFilter(chat_type=["sender", "private"]))
    register_handlers_default(personal_chats_router)
    register_handlers_moodle(personal_chats_router)
    register_handlers_courses_contents(personal_chats_router)
    register_handlers_settings(personal_chats_router)

    register_handlers_admin(personal_chats_router)

    errors_router = Router()
    register_handlers_errors(errors_router)

    dp.include_router(personal_chats_router)
    dp.include_router(group_chats_router)
    dp.include_router(errors_router)
    if TEST:
        dp.message.register(ignore, IsNotStuff())

    await set_commands(bot)
