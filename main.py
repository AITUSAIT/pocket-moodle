import asyncio
import json
import os

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import get_session, new_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from modules.app.admin.router import (AdminBotHandler, AdminHomeHandler,
                              AdminLogsHandler, AdminUserHandler,
                              AdminUsersHandler, StartBotHandler,
                              StopBotHandler)
from modules.app.api.router import get_user, update_user
from modules.app.functions import login_required, start_redis
from modules.app.user.router import (AssingmentHomeHandler, CourseHomeHandler,
                             UserHomeHandler)
from modules import database
from modules.app.admin.router import start_bot

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

        if 'user_id' in session:
            user_id = session['user_id']
            user = await database.get_dict(user_id)
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
            user['is_authenticated'] = True
            return {'user': user}

        return {}


# Privacy Policy
@aiohttp_jinja2.template("additional/PP.html")
class PrivacyPolicyHandler(web.View):

    async def get(self):
        session = await get_session(self.request)

        if 'user_id' in session:
            user_id = session['user_id']
            user = await database.get_dict(user_id)
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
            user['is_authenticated'] = True
            return {'user': user}

        return {}


# User Agreement
@aiohttp_jinja2.template("additional/UA.html")
class UserAgreementHandler(web.View):

    async def get(self):
        session = await get_session(self.request)

        if 'user_id' in session:
            user_id = session['user_id']
            user = await database.get_dict(user_id)
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
            user['is_authenticated'] = True
            return {'user': user}

        return {}


# User Agreement
@aiohttp_jinja2.template("additional/oferta.html")
class OfertaHandler(web.View):

    async def get(self):
        session = await get_session(self.request)

        if 'user_id' in session:
            user_id = session['user_id']
            user = await database.get_dict(user_id)
            user['courses'] = json.loads(user.get('courses', '{}'))
            user['gpa'] = json.loads(user.get('gpa', '{}'))
            user['att_statistic'] = json.loads(user.get('att_statistic', '{}'))
            user['is_authenticated'] = True
            return {'user': user}

        return {}


# login
@aiohttp_jinja2.template("register/login.html")
class LoginHandler(web.View):

    async def get(self):
        router = self.request.app.router
        session = await get_session(self.request)

        if 'user_id' in session:
            raise web.HTTPFound(router["me"].url_for())
        else:
            return {}

    async def post(self):
        router = self.request.app.router
        form = await self.request.post()
        user_id = str(form['user_id'])
        barcode = str(form['barcode'])
        passwd = str(form['password'])

        if await database.if_user(form['user_id']):
            passwd_crypted = await database.get_key(user_id, 'passwd')
            if passwd_crypted == database.crypt(passwd, barcode):
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
    await start_bot()
    app = web.Application()
    app['static_root_url'] = '/static'
    app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    setup(app,EncryptedCookieStorage(str.encode(os.getenv('COOKIE_KEY'))))

    app.add_routes(routes)
    app.router.add_get('/', HomeHandler, name='home')

    app.router.add_get('/privacy_policy', PrivacyPolicyHandler, name='privacy_policy')
    app.router.add_get('/user_agreement', UserAgreementHandler, name='user_agreement')
    app.router.add_get('/oferta', OfertaHandler, name='oferta')

    app.router.add_get('/about', AboutHandler, name='about')
    app.router.add_get('/admin', AdminHomeHandler, name='admin')
    app.router.add_get('/admin/bot', AdminBotHandler, name='admin_bot')
    app.router.add_get('/admin/logs', AdminLogsHandler, name='admin_logs')
    app.router.add_get('/admin/users', AdminUsersHandler, name='admin_users')
    app.router.add_get('/admin/users/{user_id}', AdminUserHandler, name='admin_user')

    app.router.add_get('/start', StartBotHandler, name='start')
    app.router.add_get('/stop', StopBotHandler, name='stop')

    app.router.add_get('/login', LoginHandler, name='login')
    app.router.add_post('/login', LoginHandler)

    app.router.add_get('/logout', LogoutHandler, name='logout')

    app.router.add_get('/me', UserHomeHandler, name='me')
    app.router.add_get('/me/{course_id}', CourseHomeHandler, name='course')
    app.router.add_get('/me/{course_id}/{ass_id}', AssingmentHomeHandler, name='assignments')

    app.add_routes([
        web.get('/api/get_user', get_user),
        web.post('/api/update_user', update_user),

        # web.get('/api/result', payment),
        # web.get('/api/result/', payment),
    ])

    return app

asyncio.run(start_redis())
web.run_app(make_app())
asyncio.run(database.close())
