import os

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from config import (DB_DB, DB_HOST, DB_PASSWD, DB_PORT, DB_USER, bot, bot_task,
                    dp, server_port)
from modules.app.api.router import get_user, health, payment, update_user
from modules.bot import main as start
from modules.classes import Suspendable
from modules.database import DB
from modules.logger import Logger

routes = web.RouteTableDef()
Logger.load_config()


async def start_bot():
    global bot_task, bot, dp
    bot_task = Suspendable(start(bot, dp))


async def start_DB():
    dsn = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
    await DB.connect(dsn)


async def make_app():
    await start_DB()
    await start_bot()
    
    app = web.Application()
    setup(app,EncryptedCookieStorage(str.encode(os.getenv('COOKIE_KEY'))))

    app.add_routes([
        web.get('/api/health', health),
        web.get('/api/get_user', get_user),
        web.post('/api/update_user', update_user),
        web.post('/api/payment', payment),
    ])

    return app

web.run_app(make_app(), port=server_port)
