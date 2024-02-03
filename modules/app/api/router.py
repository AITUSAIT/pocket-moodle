import asyncio
import hashlib
import hmac
import time

from aiogram.utils import exceptions
from aiohttp import web

import global_vars
from config import OXA_MERCHANT_KEY
from modules.bot.keyboards.purchase import purchase_btns
from modules.database import ServerDB, UserDB
from modules.database.models import User
from modules.logger import Logger
from modules.oxapay import OxaPay


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

        if not user.is_active_sub() and not await UserDB.if_msg_end_date(user.user_id):
            await UserDB.set_msg_end_date(user.user_id, 1)
            text = (
                "*Your subscription has ended\!*\n\n"
                "Available functions:\n"
                "\- Grades \(without notifications\)\n\n"
                "\- Deadlines \(without notifications\)\n\n"
                "To get access to all the features you need to purchase a subscription"
            )
            kb = purchase_btns()
            try:
                await global_vars.bot.send_message(
                    user.user_id, text, reply_markup=kb, parse_mode="MarkdownV2", disable_web_page_preview=True
                )
            except exceptions.BotBlocked:
                ...
            except exceptions.ChatNotFound:
                ...
            except exceptions.RetryAfter as e:
                await asyncio.sleep(e.timeout)
                await global_vars.bot.send_message(
                    user.user_id, text, reply_markup=kb, parse_mode="MarkdownV2", disable_web_page_preview=True
                )
            except exceptions.UserDeactivated:
                ...
            except Exception as exc:
                Logger.error(f"{user.user_id}\n{exc}\n", exc_info=True)

        if user.has_api_token() and (user.is_active_user() or user.is_active_sub()):
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


async def payment(request: web.Request):
    data: dict = await request.json()
    post_data = await request.read()

    hmac_header = request.headers.get("HMAC")
    calculated_hmac = hmac.new(OXA_MERCHANT_KEY.encode(), post_data, hashlib.sha512).hexdigest()

    Logger.info(f"Received payment callback: {data}")

    if calculated_hmac != hmac_header:
        return web.Response(text="Invalid HMAC signature", status=400)

    if data["type"] != "payment":
        return web.Response(text="OK", status=400)

    await OxaPay.verify_payment(data)
    return web.Response(text="OK", status=200)
