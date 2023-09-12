import asyncio
import time

from aiogram.utils import exceptions
from aiohttp import web

from config import bot, servers, start_time, users

from ...bot.keyboards.purchase import purchase_btns
from ...database import UserDB, ServerDB
from ...database.models import User
from ...logger import Logger
from ...oxapay import OxaPay


async def insert_user(user_id):
    global users
    user = await UserDB.get_user(user_id)
      
    users.insert(0, user)


async def get_user(request: web.Request):
    global users
    global servers
    global start_time

    if servers == []:
        servers = await ServerDB.get_servers()
        for key, val in servers.items():
            servers[key] = val

    if request.rel_url.query.get('token', None) not in servers:
        return web.json_response({
            'status': 401,
            'msg': 'Invalid token'
        })

    while 1:
        if users == []:
            if start_time is not None:
                Logger.info(f"{(time.time() - start_time)} секунд\n")
            start_time = time.time()
            users = await UserDB.get_users()
        user: User = users.pop(0)

        if not user.is_active_sub() and not await UserDB.if_msg_end_date(user.user_id):
            await UserDB.set_msg_end_date(user.user_id, 1)
            text = f"*Your subscription has ended\!*\n\n" \
                    "Available functions:\n" \
                    "\- Grades \(without notifications\)\n\n" \
                    "To get access to all the features you need to purchase a subscription"
            kb = purchase_btns()
            try:
                await bot.send_message(user.user_id, text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)
                # NEW FEATURE: send notification to app
            except exceptions.BotBlocked:
                ...
            except exceptions.ChatNotFound:
                ...
            except exceptions.RetryAfter as e:
                await asyncio.sleep(e.timeout)
                await bot.send_message(user.user_id, text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)
                # NEW FEATURE: send notification to app
            except exceptions.UserDeactivated:
                ...
            except Exception as exc:
                Logger.error(f"{user.user_id}\n{exc}\n", exc_info=True)

        if user.has_api_token():
            break

    data = {
        'status': 200,
        'user': user.to_dict()
    }
        
    return web.json_response(data)


async def update_user(request: web.Request):
    token = request.rel_url.query.get('token', None)
    post_data = await request.post()
    if token not in servers:
        data = {
            'status': 401,
            'msg': 'Invalid token'
        }

        return web.json_response(data)

    user_id = post_data['user_id']
    result = post_data['result']

    Logger.info(f"{user_id} - {result} - {servers[token].name}")

    data = {
        'status': 200,
    }
    return web.json_response(data)


async def payment(request: web.Request):
    Logger.info(f"{request.url}")
    trackId = request.rel_url.query.get('trackId', None)
    success = request.rel_url.query.get('success', None)
    status = request.rel_url.query.get('status', None)
    orderId = request.rel_url.query.get('orderId', None)

    await OxaPay.verify_payment(str(trackId), success, status, orderId)
    return web.json_response({
        'status': 200
    })