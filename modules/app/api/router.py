import asyncio
import json
import time

from aiohttp import web
from aiogram.utils import exceptions
from async_lru import alru_cache

from config import bot
from modules.oxapay import OxaPay

from ...database import DB
from ...logger import logger
from ...bot.keyboards.default import main_menu
from ...bot.keyboards.purchase import purchase_btns


users = []
start_time = None
servers = []


@alru_cache(ttl=720)
async def insert_user(user_id):
    global users
    users.insert(0, str(user_id))


async def get_user(request: web.Request):
    global users
    global servers
    global start_time

    if servers == []:
        servers = await DB.redis1.hgetall('servers')
        for key, val in servers.items():
            servers[key] = json.loads(val)

    if request.rel_url.query.get('token', None) not in servers:
        return web.json_response({
            'status': 401,
            'msg': 'Invalid token'
        })

    while 1:
        if len(users) == 0:
            if start_time is not None:
                logger.info(f"{(time.time() - start_time)} секунд\n")
            start_time = time.time()
            users = await DB.redis.keys()
            users.sort()
        user = await DB.get_dict(users[0])
        del users[0]

        if user.get('user_id', None) is None:
            continue

        if await DB.is_sleep(user['user_id']):
            continue

        user['courses'] = json.loads(user.get('courses', '{}'))
        user['gpa'] = json.loads(user.get('gpa', '{}'))
        user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
        
        if not await DB.is_active_sub(user['user_id']):
            if not await DB.check_if_msg_end_date(user['user_id']):
                await DB.set_msg_end_date(user['user_id'], 1)
                text = f"*Your subscription has ended\!*\n\n" \
                        "Available functions:\n" \
                        "\- Grades \(without notifications\)\n\n" \
                        "To get access to all the features you need to purchase a subscription"
                kb = purchase_btns()
                try:
                    await bot.send_message(user['user_id'], text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)
                except exceptions.BotBlocked:
                    await DB.set_sleep(user['user_id'])
                except exceptions.ChatNotFound:
                    await DB.set_sleep(user['user_id'])
                except exceptions.RetryAfter as e:
                    await asyncio.sleep(e.timeout)
                    await bot.send_message(user['user_id'], text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)
                except exceptions.UserDeactivated:
                    await DB.set_sleep(user['user_id'])
                except Exception as exc:
                    logger.error(f"{user['user_id']}\n{exc}\n", exc_info=True)

        if await DB.is_registered_moodle(user['user_id']):
            break

    data = {
        'status': 200,
        'user': user
    }
        
    return web.json_response(data)


async def update_user(request: web.Request):
    token = request.rel_url.query.get('token', None)
    post_data = await request.post()
    if token in servers:
        user_id = post_data['user_id']
        result = post_data['result']

        logger.info(f"{user_id} - {result} - {servers[token]['name']}")

        data = {
            'status': 200,
        }
    else:
        data = {
            'status': 401,
            'msg': 'Invalid token'
        }

    return web.json_response(data)


async def payment(request: web.Request):
    trackId = request.rel_url.query.get('trackId', None)
    success = request.rel_url.query.get('success', None)
    status = request.rel_url.query.get('status', None)
    orderId = request.rel_url.query.get('orderId', None)

    await OxaPay.verify_payment(str(trackId), success, status, orderId)
    return web.json_response({
        'status': 200
    })