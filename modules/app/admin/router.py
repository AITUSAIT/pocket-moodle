import json

import aiohttp_jinja2
from aiohttp import web

from config import bot, bot_task, dp

from ... import database
from ...app.functions import admin_required
from ...bot.functions.functions import get_diff_time
from ...bot import main as start
from ...classes import Suspendable


# home
@aiohttp_jinja2.template("admin/index.html")
class AdminHomeHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        return {'user': user}


# Bot
@aiohttp_jinja2.template("admin/bot.html")
class AdminBotHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        return {'user': user}


# Logs
@aiohttp_jinja2.template("admin/logs.html")
class AdminLogsHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        return {'user': user}


# users
@aiohttp_jinja2.template("admin/users.html")
class AdminUsersHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        users = await database.redis.keys()
        users.remove('news')
        return {'user': user, 'users': users}


# User
@aiohttp_jinja2.template("admin/user.html")
class AdminUserHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        user_id = self.request.match_info['user_id']
        user_ = await database.get_dict(user_id)
        user_['courses'] = json.loads(user_.get('courses', '{}'))
        user_['gpa'] = json.loads(user_.get('gpa', '{}'))
        user_['att_statistic'] = json.loads(user_.get('att_statistic', '{}'))
        if await database.is_active_sub(user_id):
            user_['time'] = get_diff_time(user['end_date'])
        return {'user': user, 'user_': user_}


# start Bot
class StartBotHandler(web.View):

    @admin_required
    async def get(self):
        global bot_task, bot
        if bot_task is None:
            bot_task = Suspendable(start(bot))
            return web.Response(text="Bot started!")

        if not bot_task.is_suspended():
            return web.Response(text="Bot already started!")
        else:
            bot_task.resume()
            return web.Response(text="Bot started!")


# stop Bot
class StopBotHandler(web.View):

    @admin_required
    async def get(self):
        global bot_task, bot
        if bot_task is None:
            return web.Response(text="Bot already stopped!")

        if not bot_task.is_suspended():
            bot_task.suspend()
            return web.Response(text="Bot stopped!")

        return web.Response(text="Bot already stopped!")


async def start_bot():
    global bot_task, bot, dp
    bot_task = Suspendable(start(bot, dp))
