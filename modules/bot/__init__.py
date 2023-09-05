from aiogram.types import BotCommand

from .handlers.admin import register_handlers_admin
from .handlers.default import register_handlers_default
from .handlers.moodle import register_handlers_moodle
from .handlers.purchase import register_handlers_purchase
from .handlers.secondary import register_handlers_secondary
from .handlers.settings import register_handlers_settings


async def set_commands(bot):
    commands = [
        BotCommand(command="/start", description="Start | Info"),
        BotCommand(command="/help", description="Help | Commands"),

        BotCommand(command="/submit_assignment", description="Submit Assignment"),
        BotCommand(command="/check_finals", description="Check Finals"),

        BotCommand(command="/update", description="Update info"),
        
        BotCommand(command="/promocode", description="Activate a promo code"),
        BotCommand(command="/purchase", description="Purchase subscription"),
        BotCommand(command="/register", description="Register account"),
        
        BotCommand(command="/convert", description="Convert to PDF file"),
        
        BotCommand(command="/create_promocode", description="(Admin)"),
        BotCommand(command="/send_msg", description="(Admin)"),
        BotCommand(command="/get", description="(Admin)")
    ]
    await bot.set_my_commands(commands)


async def main(bot, dp):
    register_handlers_admin(dp)
    
    register_handlers_default(dp)
    register_handlers_moodle(dp)
    register_handlers_purchase(dp)
    register_handlers_settings(dp)
    
    register_handlers_secondary(dp)
    
    await set_commands(bot)

    await dp.start_polling()
