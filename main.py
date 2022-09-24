import asyncio
import os

from aiohttp import web
from aiohttp_session import new_session, get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2
import jinja2
from app.api.router import get_user, payment, update_user

from app.functions import admin_required, login_required, start_redis
from app.admin.router import AdminHomeHandler, StopBotHandler, StartBotHandler
from app.user.router import AssingmentHomeHandler, CourseHomeHandler, UserHomeHandler
from bot.objects import aioredis

routes = web.RouteTableDef()



class HomeHandler(web.View):

    async def get(self):
        router = self.request.app.router
        session = await get_session(self.request)

        if 'user_id' in session:
            raise web.HTTPFound(router["me"].url_for())
        else:
            raise web.HTTPFound(router["about"].url_for())


# about
@aiohttp_jinja2.template("about.html")
class AboutHandler(web.View):

    async def get(self):
        session = await get_session(self.request)

        return {}


# login
@aiohttp_jinja2.template("register/login.html")
class LoginHandler(web.View):

    async def get(self):
        return {}

    async def post(self):
        router = self.request.app.router
        form = await self.request.post()
        user_id = str(form['user_id'])
        barcode = str(form['barcode'])
        passwd = str(form['password'])

        if await aioredis.if_user(form['user_id']):
            passwd_crypted = await aioredis.get_key(user_id, 'passwd')
            if passwd_crypted == aioredis.crypt(passwd, barcode):
                session = await new_session(self.request)
                session["user_id"] = form['user_id']
                raise web.HTTPFound(router["home"].url_for())
            else:
                return { 'message': 'Wrong ID, barcode or password'}
        else:
            return { 'message': 'Wrong ID, barcode or password'}


# logout 
class LogoutHandler(web.View):

    @login_required
    async def get(self):
        session = await get_session(self.request)
        del session["user_id"]
        raise web.HTTPSeeOther(location="/")


async def make_app():
    app = web.Application()
    app['static_root_url'] = '/static'
    app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    setup(app,EncryptedCookieStorage(str.encode(os.getenv('COOKIE_KEY'))))

    app.add_routes(routes)
    app.router.add_get('/', HomeHandler, name='home')

    app.router.add_get('/about', AboutHandler, name='about')
    app.router.add_get('/admin', AdminHomeHandler, name='admin')

    app.router.add_get('/login', LoginHandler, name='login')
    app.router.add_post('/login', LoginHandler)

    app.router.add_get('/logout', LogoutHandler, name='logout')

    app.router.add_get('/start', StartBotHandler, name='start')
    app.router.add_get('/stop', StopBotHandler, name='stop')

    app.router.add_get('/me', UserHomeHandler, name='me')
    app.router.add_get('/me/{course_id}', CourseHomeHandler, name='course')
    app.router.add_get('/me/{course_id}/{ass_id}', AssingmentHomeHandler, name='assignments')

    app.add_routes([
        web.get('/api/get_user', get_user),
        web.post('/api/update_user', update_user),

        web.get('/api/payment', payment),
    ])

    return app

asyncio.run(start_redis())
web.run_app(make_app())
asyncio.run(aioredis.close())
