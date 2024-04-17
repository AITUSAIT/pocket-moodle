import os

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiogram.dispatcher.webhook import get_new_configured_app

import global_vars
from config import DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER, SERVER_HOST, SERVER_PORT, WEBHOOK_URL
from modules.app.api.router import get_user, health, update_user
from modules.database import DB
from modules.logger import Logger

routes = web.RouteTableDef()
Logger.load_config()


async def connect_db():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def on_startup(_: web.Application):
    # register handlers

    # Get current webhook status
    webhook = await global_vars.bot.get_webhook_info()

    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        if not webhook.url:
            await global_vars.bot.delete_webhook()

        # Set new URL for webhook
        # await global_vars.bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, 'rb'))
        # If you want to use free certificate signed by LetsEncrypt you need to set only URL without sending certificate.


async def on_shutdown(_: web.Application):
    """
    Graceful shutdown. This method is recommended by aiohttp docs.
    """
    await global_vars.bot.delete_webhook()


async def make_app():
    await connect_db()

    app = get_new_configured_app(global_vars.dp, path="/webhook")
    # app.on_startup.append(on_startup)
    # app.on_shutdown.append(on_shutdown)

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
