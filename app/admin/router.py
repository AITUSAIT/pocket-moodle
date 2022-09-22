import asyncio
from aiohttp import web
import aiohttp_jinja2

from app.functions import admin_required

from bot.module import main as start_bot
from config import Suspendable, bot, bot_task

# home
@aiohttp_jinja2.template("admin/home.html")
class AdminHomeHandler(web.View):

    @admin_required
    async def get(self):
        user = self.request.user
        return {'user': user}


# start Bot
class StartBotHandler(web.View):

    @admin_required
    async def get(self):
        global bot_task, bot
        if bot_task is None:
            bot_task = Suspendable(start_bot(bot))
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

