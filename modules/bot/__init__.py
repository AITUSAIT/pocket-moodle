from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)

from modules.bot.handlers.mailing import register_mailing_handlers

from .handlers.admin import register_handlers_admin
from .handlers.course_contents import register_handlers_courses_contents
from .handlers.default import register_handlers_default
from .handlers.group import register_handlers_groups
from .handlers.moodle import register_handlers_moodle
from .handlers.secondary import register_handlers_secondary
from .handlers.settings import register_handlers_settings
from .throttling import ThrottlingMiddleware


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),
        BotCommand(command="/submit_assignment", description="Submit Assignment"),
        BotCommand(command="/check_finals", description="Check Finals"),
        BotCommand(command="/register", description="Register account"),
        BotCommand(command="/promocode", description="Activate a promo code"),
        BotCommand(command="/purchase", description="Purchase subscription"),
        BotCommand(command="/convert", description="Convert to PDF file"),
        BotCommand(command="/update", description="Update info"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())

    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),
        BotCommand(command="/check_finals", description="Check Finals"),
        BotCommand(command="/register", description="Register account"),
        BotCommand(command="/convert", description="Convert to PDF file"),
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
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/get_deadlines", description="Get deadlines (Group)"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeAllChatAdministrators())


async def register_bot_handlers(bot: Bot, dp: Dispatcher):
    dp.message.middleware(ThrottlingMiddleware(limit=0.5, key_prefix="antiflood"))
    dp.callback_query.middleware(ThrottlingMiddleware(limit=0.5, key_prefix="antiflood"))
    register_mailing_handlers(dp)

    register_handlers_groups(dp)

    register_handlers_admin(dp)

    register_handlers_default(dp)
    register_handlers_moodle(dp)
    register_handlers_courses_contents(dp)
    register_handlers_settings(dp)

    register_handlers_secondary(dp)

    await set_commands(bot)
