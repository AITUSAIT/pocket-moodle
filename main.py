import os

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import global_vars
from config import DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER, SERVER_HOST, SERVER_PORT, WEBHOOK_PATH, WEBHOOK_URL
from modules.app.api.router import get_user, health, update_user
from modules.database import DB
from modules.logger import Logger

routes = web.RouteTableDef()
Logger.load_config()


async def connect_db():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def on_startup(_: web.Application):
    await global_vars.bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(_: web.Application):
    """
    Graceful shutdown. This method is recommended by aiohttp docs.
    """
    await global_vars.bot.delete_webhook()


async def make_app():
    await connect_db()

    global_vars.dp.startup.register(on_startup)
    app = web.Application()
    webhook_request_handler = SimpleRequestHandler(
        dispatcher=global_vars.dp,
        bot=global_vars.bot,
    )
    webhook_request_handler.register(app, WEBHOOK_PATH)
    setup_application(app, global_vars.dp, bot=global_vars.bot)

    setup(app, EncryptedCookieStorage(str.encode(os.getenv("COOKIE_KEY", "COOKIE"))))

    app.add_routes(
        [
            web.get("/api/health", health),
            web.get("/api/get_user", get_user),
            web.post("/api/update_user", update_user),
        ]
    )

    return app


web.run_app(make_app(), host=SERVER_HOST, port=SERVER_PORT)
