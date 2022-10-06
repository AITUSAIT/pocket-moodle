import json
from sys import exc_info
import time

from aiohttp import web
from bot.keyboards.default import main_menu

from config import tokens, bot, robo_passwd_2
from bot.objects.logger import logger
from bot.objects import aioredis
from robokassa import result_payment

users = []
start_time = None


async def get_user(request):
    global users
    global start_time
    if request.rel_url.query.get('token', None) in tokens:
        while 1:
            if len(users) == 0:
                if start_time is not None:
                    logger.info(f"{(time.time() - start_time)} секунд\n")
                start_time = time.time()
                users = await aioredis.redis.keys()
                users.sort()
                users.remove('news')
            user = await aioredis.get_dict(users[0])
            del users[0]
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
            if await aioredis.is_active_sub(user['user_id']) and await aioredis.is_registered_moodle(user['user_id']):
                break

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


async def update_user(request):
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
        res, id = result_payment(robo_passwd_2, request.rel_url.query_string)
        if res == 'bad sign':
            text = "An error occurred during payment"
        else:
            text = "The payment was successful!"
        
        kb = main_menu()
        await bot.send_message(id, text, reply_markup=kb)
        return web.Response(res)
    except Exception as exc:
        logger.error(exc, exc_info=True)
