import asyncio

import global_vars
from modules.bot import register_bot_handlers
from modules.logger import Logger

Logger.load_config()


async def run():
    Logger.info("Registering handlers...")
    await register_bot_handlers(global_vars.bot, global_vars.dp)

    Logger.info("Starting polling...")
    await global_vars.dp.start_polling(global_vars.bot, handle_signals=False)


asyncio.run(run())
