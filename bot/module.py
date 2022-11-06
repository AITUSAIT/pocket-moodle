import os

import dotenv
from aiogram.types import BotCommand
from bot.handlers.admin import register_handlers_admin

from bot.handlers.default import register_handlers_default
from bot.handlers.inline import register_handlers_inline
from bot.handlers.moodle import register_handlers_moodle
from bot.handlers.purchase import register_handlers_purchase
from bot.handlers.secondary import register_handlers_secondary

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

        BotCommand(command="/get_grades", description="Get grades"),
        BotCommand(command="/get_deadlines", description="Get deadlines"),
        BotCommand(command="/get_attendance", description="Get attendance"),
        BotCommand(command="/check_finals", description="Check Finals"),
        BotCommand(command="/update", description="Update info now"),
        
        BotCommand(command="/info", description="Info about organization"),

        BotCommand(command="/photos_to_pdf", description="Convert to PDF file"),

        BotCommand(command="/promocode", description="Activate a promo code"),
        BotCommand(command="/purchase", description="Purchase subscription"),
        BotCommand(command="/register_moodle", description="Register Moodle account"),
        
        BotCommand(command="/msg_to_admin", description="Msg to Admin")
    ]
    await bot.set_my_commands(commands)


async def main(bot, dp):
    register_handlers_default(dp)
    register_handlers_moodle(dp)
    register_handlers_purchase(dp)
    
    register_handlers_admin(dp)

    register_handlers_secondary(dp)
    register_handlers_inline(dp)
    
    await set_commands(bot)

    await dp.start_polling()
