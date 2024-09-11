from copy import copy
from datetime import timedelta

from modules.database import CourseDB, UserDB
from modules.database.models import GroupedCourse, User

from modules.bot.functions.functions import escape_md, get_diff_time


async def filtered_deadlines_days(day: int, user: User) -> str:
    text = ""
    url = "https://moodle.astanait.edu.kz/mod/assign/view.php?id="
    url_course = "https://moodle.astanait.edu.kz/course/view.php?id="
    courses = await CourseDB.get_courses(user.user_id)

    for course in courses.values():
        state = 1
        course_state = 0
        for deadline in [d for d in course.deadlines.values() if not d.submitted]:
            diff_time = get_diff_time(deadline.due)
            if diff_time > timedelta(days=0) and diff_time < timedelta(days=day):
                if state:
                    state = 0
                    text += f"[{escape_md(course.name)}]({escape_md(url_course)}{escape_md(course.course_id)}):"
                course_state = 1
                text += f"\n    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
                text += f"\n    {escape_md(deadline.due)}"
                text += f"\n    Remaining: {escape_md(diff_time)}"
                text += "\n"
        if course_state:
            text += "\n\n"
    return text


async def filtered_deadlines_course(course_id: int, user: User) -> str:
    text = ""

    url = "https://moodle.astanait.edu.kz/mod/assign/view.php?id="
    url_course = "https://moodle.astanait.edu.kz/course/view.php?id="
    courses = await CourseDB.get_courses(user.user_id, True)
    course = courses[str(course_id)]
    state = 1
    for deadline in [_ for _ in course.deadlines.values() if not _.submitted]:
        diff_time = get_diff_time(deadline.due)
        if diff_time > timedelta(days=0):
            if state:
                state = 0
                text += f"[{escape_md(course.name)}]({escape_md(url_course)}{escape_md(course.course_id)}):"
            text += f"\n    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
            text += f"\n    {escape_md(deadline.due)}"
            text += f"\n    Remaining: {escape_md(diff_time)}"
            text += "\n"
    return text


async def filtered_deadlines_days_for_group(day: int, users: list[int]) -> list[str]:
    def filter_by_words(name: str):
        words = ["Midterm", "Endterm", "Final Exam"]

        return name in words

    text = [""]
    index = 0
    url = "https://moodle.astanait.edu.kz/mod/assign/view.php?id="
    url_course = "https://moodle.astanait.edu.kz/course/view.php?id="

    grouped_courses: dict[str, GroupedCourse] = {}
    for user_id in users:
        user = await UserDB.get_user(user_id)
        if not user:
            continue

        users_courses = copy(await CourseDB.get_courses(user.user_id))
        for key, val in users_courses.items():
            if key not in grouped_courses:
                grouped_courses[key] = GroupedCourse(
                    course_id=val.course_id, name=val.name, active=val.active, grades=copy(val.grades), deadlines={}
                )
            grouped_courses[key].deadlines[str(user.user_id)] = val.deadlines

    temp = []

    for grouped_course in grouped_courses.values():
        state = 1
        course_state = 0
        for deadlines in grouped_course.deadlines.values():
            for deadline in [d for d in deadlines.values() if d.id not in temp and not filter_by_words(d.name)]:
                temp.append(deadline.id)

                diff_time = get_diff_time(deadline.due)
                if diff_time > timedelta(days=0) and diff_time < timedelta(days=day):
                    if state:
                        state = 0
                        text[
                            index
                        ] += f"[{escape_md(grouped_course.name)}]({escape_md(url_course)}{escape_md(grouped_course.course_id)}):\n"
                    course_state = 1
                    text[index] += f"    [{escape_md(deadline.name)}]({escape_md(url)}{escape_md(deadline.id)})"
                    text[index] += f"\n    {escape_md(deadline.due)}"
                    text[index] += f"\n    Remaining: {escape_md(diff_time)}"
                    text[index] += "\n\n"
                    if len(text[index]) > 3000:
                        index += 1
                        text.append("")
        if course_state:
            text[index] += "\n\n"
    return text


async def get_deadlines_local_by_days_group(users: list[int], day: int) -> list[str] | None:
    text = await filtered_deadlines_days_for_group(day, users)

    return text if text[0] != "" else None


async def get_deadlines_local_by_days(user: User, day: int) -> str | None:
    text = await filtered_deadlines_days(day, user)

    return text if len(text.replace("\n", "")) != 0 else None


async def get_deadlines_local_by_course(user: User, course_id: int) -> str | None:
    text = await filtered_deadlines_course(course_id, user)

    return text if len(text.replace("\n", "")) != 0 else None
