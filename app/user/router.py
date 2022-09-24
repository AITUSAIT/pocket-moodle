from aiohttp import web
import aiohttp_jinja2

from app.functions import login_required


# me
@aiohttp_jinja2.template("user/me.html")
class UserHomeHandler(web.View):

    @login_required
    async def get(self):
        user = self.request.user
        return {'user': user}


# course
@aiohttp_jinja2.template("user/course.html")
class CourseHomeHandler(web.View):

    @login_required
    async def get(self):
        user = self.request.user
        return {'user': user, 'course_id': self.request.match_info['course_id']}


# assignment
@aiohttp_jinja2.template("user/assignment.html")
class AssingmentHomeHandler(web.View):

    @login_required
    async def get(self):
        user = self.request.user
        return {
            'user': user,
            'course_id': self.request.match_info['course_id'],
            'assignment_id': self.request.match_info['ass_id'],
            }

