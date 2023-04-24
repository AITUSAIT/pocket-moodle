import json
import time

from aiohttp import web

from config import bot, prices, ROBO_PASSWD_2, tokens
from modules.oxapay import OxaPay

from ... import database, logger
from ...logger import logger
from ...bot.keyboards.default import main_menu
from ...bot.keyboards.purchase import purchase_btns

users = []
start_time = None


async def get_user(request: web.Request):
    global users
    global start_time
    if request.rel_url.query.get('token', None) not in tokens:
        return web.json_response({
            'status': 401,
            'msg': 'Invalid token'
        })

    while 1:
        if len(users) == 0:
            if start_time is not None:
                logger.info(f"{(time.time() - start_time)} секунд\n")
            start_time = time.time()
            users = await database.redis.keys()
            users.sort()
            if 'news' in users:
                users.remove('news')
        user = await database.get_dict(users[0])
        del users[0]

        if user.get('user_id', None) is None:
            continue

        if await database.is_sleep(user['user_id']):
            continue

        user['courses'] = json.loads(user.get('courses', '{}'))
        user['gpa'] = json.loads(user.get('gpa', '{}'))
        user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
        
        if not await database.is_active_sub(user['user_id']):
            if not await database.check_if_msg_end_date(user['user_id']):
                await database.set_msg_end_date(user['user_id'], 1)
                text = f"*Your subscription has ended\!*\n\n" \
                        "Available functions:\n" \
                        "- Grades \(without notifications\)\n\n" \
                        "To get access to all the features you need to purchase a subscription"
                kb = purchase_btns()
                try:
                    await bot.send_message(user['user_id'], text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)
                except:
                    ...

        if await database.is_registered_moodle(user['user_id']):
            break

    data = {
        'status': 200,
        'user': user
    }
        
    return web.json_response(data)


async def update_user(request: web.Request):
    token = request.rel_url.query.get('token', None)
    post_data = await request.post()
    if token in tokens:
        user_id = post_data['user_id']
        result = post_data['result']

        logger.info(f"{user_id} - {result} - {tokens[token]}")

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