from datetime import timedelta

from modules.database import CourseDB
from modules.database.models import User
from .functions import get_diff_time


async def filtered_deadlines_days(day: int, user: User) -> str:
    text = ''
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    courses = await CourseDB.get_courses(user.user_id)

    for course in courses.values():
        state = 1
        course_state = 0
        for deadline in [ d for d in course.deadlines.values() if not d.submitted ]:
            diff_time = get_diff_time(deadline.due)
            if diff_time>timedelta(days=0) and diff_time<timedelta(days=day):
                if state:
                    state = 0
                    text += f"[{course.name}]({url_course}{course.course_id}):"
                course_state = 1
                text += f"\n    [{deadline.name}]({url}{deadline.id})"
                text += f"\n    {deadline.due}"
                text += f"\n    Remaining: {diff_time}"
                text += '\n'
        if course_state:
            text += '\n\n'
    return text


async def filtered_deadlines_course(id: int, user: User) -> str:
    text = ''
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    course = await CourseDB.get_course(user.user_id, id)
    state = 1
    for deadline in [ d for d in course.deadlines.values() if not d.submitted ]:
        diff_time = get_diff_time(deadline.due)
        if diff_time>timedelta(days=0):
            if state:
                state = 0
                text += f"[{course.name}]({url_course}{course.course_id}):"
            text += f"\n    [{deadline.name}]({url}{deadline.id})"
            text += f"\n    {deadline.due}"
            text += f"\n    Remaining: {diff_time}"
            text += '\n'
    return text


async def get_deadlines_local_by_days(user: User, day: int) -> str:
    text = await filtered_deadlines_days(day, user)

    return text if len(text.replace('\n', ''))!=0 else None


async def get_deadlines_local_by_course(user: dict, id: int) -> str:
    text = await filtered_deadlines_course(id, user)

    return text if len(text.replace('\n', ''))!=0 else None
