import os

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import global_vars
from config import DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER, SERVER_PORT
from modules.app.api.router import get_user, health, update_user
from modules.bot import main as start
from modules.classes import Suspendable
from modules.database import DB
from modules.logger import Logger

routes = web.RouteTableDef()
Logger.load_config()


async def start_bot():
    global_vars.bot_task = Suspendable(start(global_vars.bot, global_vars.dp))


async def connect_db():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def make_app():
    await connect_db()
    await start_bot()

    app = web.Application()
    setup(app, EncryptedCookieStorage(str.encode(os.getenv("COOKIE_KEY"))))

    app.add_routes(
        [
            web.get("/api/health", health),
            web.get("/api/get_user", get_user),
            web.post("/api/update_user", update_user),
        ]
    )

    return app


web.run_app(make_app(), port=SERVER_PORT)
