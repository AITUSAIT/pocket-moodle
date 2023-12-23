from datetime import timedelta

from modules.database import CourseDB, UserDB
from modules.database.models import Course, Deadline, User
from .functions import get_diff_time

from aiogram.utils.markdown import escape_md


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
                    text += f"[{escape_md(course.name)}]({escape_md(url_course)}{escape_md(course.course_id)}):"
                course_state = 1
                text += f"\n    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
                text += f"\n    {escape_md(deadline.due)}"
                text += f"\n    Remaining: {escape_md(diff_time)}"
                text += '\n'
        if course_state:
            text += '\n\n'
    return text


async def filtered_deadlines_course(id: int, user: User) -> str:
    text = ['']
    index = 0
    
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    course = await CourseDB.get_course(user.user_id, id)
    state = 1
    for deadline in [ d for d in course.deadlines.values() if not d.submitted ]:
        diff_time = get_diff_time(deadline.due)
        if diff_time>timedelta(days=0):
            if state:
                state = 0
                text[index] += f"[{escape_md(course.name)}]({escape_md(url_course)}{escape_md(course.course_id)}):"
            text[index] += f"\n    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
            text[index] += f"\n    {escape_md(deadline.due)}"
            text[index] += f"\n    Remaining: {escape_md(diff_time)}"
            text[index] += '\n'
            if len(text[index]) > 3000:
                index += 1
                text.append('')
    return text


async def filtered_deadlines_days_for_group(day: int, users: list[User]) -> str:
    text = ''
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    
    courses = {}
    for user_id in users:
        user = await UserDB.get_user(user_id)
        users_courses: dict[str, Course] = await CourseDB.get_courses(user.user_id)
        for key, val in users_courses.items():
            if key not in courses:
                courses[key] = {
                    "course": val,
                    "deadlines": {}
                }
            courses[key]["deadlines"][str(user.user_id)] = val.deadlines

    temp = []

    for course_d in courses.values():
        course: Course = course_d["course"]
        state = 1
        course_state = 0
        for deadlines in course_d["deadlines"].values():
            for deadline in [ d for d in deadlines.values() if d.id not in temp ]:
                deadline: Deadline
                temp.append(deadline.id)
                
                diff_time = get_diff_time(deadline.due)
                if diff_time>timedelta(days=0) and diff_time<timedelta(days=day):
                    if state:
                        state = 0
                        text += f"[{escape_md(course.name)}]({escape_md(url_course)}{escape_md(course.course_id)}):"
                    course_state = 1
                    text += f"\n    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
                    text += f"\n    {escape_md(deadline.due)}"
                    text += f"\n    Remaining: {escape_md(diff_time)}"
                    text += '\n'
        if course_state:
            text += '\n\n'
    return text


async def get_deadlines_local_by_days_group(users: list[User], day: int) -> str:
    text = await filtered_deadlines_days_for_group(day, users)

    return text if len(text.replace('\n', ''))!=0 else None


async def get_deadlines_local_by_days(user: User, day: int) -> str:
    text = await filtered_deadlines_days(day, user)

    return text if len(text.replace('\n', ''))!=0 else None


async def get_deadlines_local_by_course(user: dict, id: int) -> str:
    text = await filtered_deadlines_course(id, user)

    return text if len(text.replace('\n', ''))!=0 else None
