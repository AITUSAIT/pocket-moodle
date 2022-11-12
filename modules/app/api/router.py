import json
import time

from aiohttp import web

from config import bot, prices, robo_passwd_2, tokens
from robokassa import result_payment

from ... import database, logger
from ...logger import logger
from ...bot.keyboards.default import main_menu
from ...bot.keyboards.purchase import purchase_btns

users = []
start_time = None


async def get_user(request: web.Request):
    global users
    global start_time
    if request.rel_url.query.get('token', None) in tokens:
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
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))

            if user.get('user_id', None) is None:
                continue

            if await database.is_sleep(user['user_id']):
                continue

            if await database.is_active_sub(user['user_id']) and await database.is_registered_moodle(user['user_id']):
                break

            if not await database.is_active_sub(user['user_id']):
                if not await database.check_if_msg_end_date(user['user_id']):
                    await database.set_msg_end_date(user['user_id'], 1)
                    text = f"*Your subscription has ended\!*\n\nApply for a new one or contact the [Administration](t\.me/pocket_moodle_chat) to find out if there are any active promotions"
                    kb = purchase_btns()
                    await bot.send_message(user['user_id'], text, reply_markup=kb, parse_mode='MarkdownV2', disable_web_page_preview=True)


        data = {
            'status': 200,
            'user': user
        }
    else:
        data = {
            'status': 401,
            'msg': 'Invalid token'
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
    try:
        res, id, cost = result_payment(robo_passwd_2, request.rel_url.query_string)
        user_id = int(await database.redis1.zscore('robokassa', id))

        if res == 'bad sign':
            text = "An error occurred during payment"
        else:
            user = await database.get_dict(user_id)
            payment_state = False
            for key, value in prices.items():
                if cost == value:
                    await database.activate_subs(user_id, (int(key)*30))
                    text = f"You have been added {int(key)*30} days of subscription!"
                    payment_state = True
                    break
            enddate_str = await database.get_key(user_id, 'end_date')
            if payment_state:
                logger.info(f"{user_id} {key} {user['end_date']} -> {enddate_str}")
            else:
                text = "An error occurred during payment\n\nWrite to @dake_duck to solve this problem"
                logger.error(f"{user_id} Error {user['end_date']} -> {enddate_str}")

                        
        kb = main_menu()
        await bot.send_message(user_id, text, reply_markup=kb)
        return web.Response(text=res)
    except Exception as exc:
        logger.error(exc, exc_info=True)
