import asyncio
import os

import dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import BotCommand

from bot.handlers.default import register_handlers_default
from bot.objects.logger import logger
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

        BotCommand(command="/register_moodle", description="Register Moodle account"),
        BotCommand(command="/demo", description="Activate 1 month demo"),
        
        BotCommand(command="/msg_to_admin", description="Msg to Admin"),
        BotCommand(command="/get_logfile",description="Get LogFile (admin)"),
    ]
    await bot.set_my_commands(commands)


async def main(bot):
    dp = Dispatcher(bot, storage=MemoryStorage())

    register_handlers_default(dp)
    register_handlers_moodle(dp)
    register_handlers_purchase(dp)
    register_handlers_secondary(dp)
    
    await set_commands(bot)

    await dp.start_polling()




if __name__ == '__main__':
    asyncio.run(main())
