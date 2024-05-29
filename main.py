import asyncio
import os
from contextlib import suppress
from typing import Any, AsyncGenerator

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import global_vars
from config import DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER, SERVER_PORT
from modules.app.api.router import get_user, health, update_user
from modules.bot import register_bot_handlers
from modules.database import DB
from modules.logger import Logger

routes = web.RouteTableDef()
Logger.load_config()


async def connect_db():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def run_bot_task(_) -> AsyncGenerator[Any, None]:
    async def start_bot():
        await global_vars.dp.start_polling(global_vars.bot, handle_signals=False)

    task = asyncio.create_task(start_bot())

    yield

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def make_app():
    await connect_db()

    await register_bot_handlers(global_vars.bot, global_vars.dp)

    app = web.Application()
    app.cleanup_ctx.append(run_bot_task)

    setup(app, EncryptedCookieStorage(str.encode(os.getenv("COOKIE_KEY", "COOKIE"))))

    app.add_routes(
        [
            web.get("/api/health", health),
            web.get("/api/get_user", get_user),
            web.post("/api/update_user", update_user),
        ]
    )

    return app


web.run_app(make_app(), port=SERVER_PORT)
