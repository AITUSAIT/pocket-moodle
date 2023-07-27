import asyncio
import os

import dotenv
from aiogram.types import BotCommand

from modules.bot.handlers.calendar import register_handlers_calendar

from .handlers.admin import register_handlers_admin
from .handlers.default import register_handlers_default
from .handlers.inline import register_handlers_inline
from .handlers.moodle import register_handlers_moodle
from .handlers.purchase import register_handlers_purchase
from .handlers.secondary import register_handlers_secondary
from .handlers.settings import register_handlers_settings
from ..scheduler import EventsScheduler

dotenv.load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_DB = os.getenv('REDIS_DB')
REDIS_USER = os.getenv('REDIS_USER')
REDIS_PASSWD = os.getenv('REDIS_PASSWD')


async def set_commands(bot):
    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),

        BotCommand(command="/submit_assignment", description="Submit Assignment"),
        BotCommand(command="/check_finals", description="Check Finals"),

        BotCommand(command="/update", description="Update info"),
        BotCommand(command="/update_full", description="Reload all info"),
        
        BotCommand(command="/promocode", description="Activate a promo code"),
        BotCommand(command="/purchase", description="Purchase subscription"),
        BotCommand(command="/register_moodle", description="Register Moodle account"),
        
        BotCommand(command="/convert", description="Convert to PDF file"),
        
        BotCommand(command="/create_promocode", description="(Admin)"),
        BotCommand(command="/send_msg", description="(Admin)"),
        BotCommand(command="/get", description="(Admin)")
    ]
    await bot.set_my_commands(commands)


async def main(bot, dp):
    # asyncio.create_task(EventsScheduler.start_scheduler())

    register_handlers_admin(dp)
    
    register_handlers_default(dp)
    register_handlers_moodle(dp)
    register_handlers_calendar(dp)
    register_handlers_settings(dp)
    register_handlers_purchase(dp)
    

    register_handlers_secondary(dp)
    register_handlers_inline(dp)
    
    await set_commands(bot)

    await dp.start_polling()
