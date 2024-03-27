import time
from typing import Iterable

from aiohttp import web

import global_vars
from modules.database import ServerDB, UserDB
from modules.database.models import User
from modules.logger import Logger


def require_query_params(request: web.Request, query_params: Iterable[str]) -> str | None:
    for query_param in query_params:
        if request.rel_url.query.get(query_param) is None:
            return query_param
    return None


async def health(_: web.Request):
    return web.Response(text="OK", status=200)


async def get_user(request: web.Request):
    if global_vars.SERVERS == {}:
        global_vars.SERVERS = await ServerDB.get_servers()
        for key, val in global_vars.SERVERS.items():
            global_vars.SERVERS[key] = val

    if request.rel_url.query.get("token", None) not in global_vars.SERVERS:
        return web.json_response({"status": 401, "msg": "Invalid token"}, status=401)

    while 1:
        if global_vars.USERS == []:
            if global_vars.START_TIME is not None:
                Logger.info(f"{(time.time() - global_vars.START_TIME)} секунд\n")
            global_vars.START_TIME = time.time()
            global_vars.USERS = await UserDB.get_users()
        user: User = global_vars.USERS.pop(0)

        if user.has_api_token() and user.is_active_user():
            break

    return web.json_response(data={"status": 200, "user": user.to_dict()}, status=200)


async def update_user(request: web.Request):
    missing_query_param = require_query_params(request=request, query_params=("token",))
    if missing_query_param:
        status = 403
        return web.json_response(
            data={"status": status, "msg": f"Missing query param {missing_query_param}"}, status=status
        )

    token = request.rel_url.query["token"]
    post_data = await request.post()
    server = global_vars.SERVERS.get(token)
    if not server:
        status = 401
        return web.json_response(data={"status": status, "msg": "Invalid token"}, status=status)

    user_id = str(post_data["user_id"])
    result = str(post_data["result"])

    Logger.info(f"{user_id} - {result} - {server.name}")
    status = 200
    return web.json_response(data={"status": status, "msg": "OK"}, status=status)
