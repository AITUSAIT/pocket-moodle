import time

from aiohttp import web

import global_vars
from modules.database import ServerDB, UserDB
from modules.database.models import User
from modules.logger import Logger


async def health(_: web.Request):
    return web.Response(text="OK", status=200)


async def get_user(request: web.Request):
    if global_vars.SERVERS == []:
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
    token = request.rel_url.query.get("token", None)
    post_data = await request.post()
    if token not in global_vars.SERVERS:
        data = {"status": 401, "msg": "Invalid token"}

        return web.json_response(data, status=data["status"])

    user_id = post_data["user_id"]
    result = post_data["result"]

    Logger.info(f"{user_id} - {result} - {global_vars.SERVERS[token].name}")

    return web.json_response(data={"status": 200, "msg": "OK"}, status=200)
