import json
import os
from typing import Any, Awaitable, Callable

import dotenv
from aiohttp import web
from aiohttp_session import get_session

from .. import database

_Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def login_required(func: _Handler) -> _Handler:
    async def wrapped(handler: web.View, *args: Any, **kwargs: Any) -> web.StreamResponse:
        app = handler.request.app
        router = app.router
        session = await get_session(handler.request)

        if "user_id" not in session:
            return web.HTTPFound(router["login"].url_for())

        user_id = session["user_id"]
        user = await database.get_dict(user_id)
        user['courses'] = json.loads(user.get('courses', '{}'))
        user['gpa'] = json.loads(user.get('gpa', '{}'))
        user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
        user['is_authenticated'] = True
        handler.request.user = user
        return await func(handler, *args, **kwargs)

    return wrapped


def admin_required(func: _Handler) -> _Handler:
    async def wrapped(handler: web.View, *args: Any, **kwargs: Any) -> web.StreamResponse:
        app = handler.request.app
        router = app.router
        session = await get_session(handler.request)

        if "user_id" not in session:
            return web.HTTPFound(router["login"].url_for())

        user_id = session['user_id']
        user = await database.get_dict(user_id)
        user['courses'] = json.loads(user.get('courses', '{}'))
        user['gpa'] = json.loads(user.get('gpa', '{}'))
        user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
        user['is_authenticated'] = True
        handler.request.user = user
        if "role" not in handler.request.user or handler.request.user['role'] != 'admin':
            return web.Response(text=f"User {user['user_id']} are not Admin")
        return await func(handler, *args, **kwargs)

    return wrapped


def htmlResponse(path: str) -> web.Response:
    text = open(f'{path}.html', 'r').read()
    return web.Response(text=text, content_type='text/html')


async def start_redis():
    dotenv.load_dotenv()

    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    REDIS_DB = os.getenv('REDIS_DB')
    REDIS_USER = os.getenv('REDIS_USER') or ""
    REDIS_PASSWD = os.getenv('REDIS_PASSWD')

    await database.start_redis(
        REDIS_USER,
        REDIS_PASSWD,
        REDIS_HOST,
        REDIS_PORT,
        REDIS_DB
    )