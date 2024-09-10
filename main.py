import asyncio

import global_vars
from config import DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER
from modules.bot import register_bot_handlers
from modules.database import DB
from modules.logger import Logger

Logger.load_config()


async def connect_db():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def run():
    Logger.info("Connecting to DB...")
    await connect_db()
    Logger.info("Registering handlers...")
    await register_bot_handlers(global_vars.bot, global_vars.dp)

    Logger.info("Starting polling...")
    await global_vars.dp.start_polling(global_vars.bot, handle_signals=False)


asyncio.run(run())
