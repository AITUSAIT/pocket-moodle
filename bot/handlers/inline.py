from datetime import timedelta
import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from fuzzywuzzy import process

from bot.functions.functions import clear_MD, get_diff_time
from bot.functions.rights import IsUser
from bot.objects import aioredis


async def show_courses_list(inline_query: types.InlineQuery):
    user_id = inline_query.from_user.id
    courses = json.loads(await aioredis.get_key(user_id, 'courses'))
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='

    results = []
    if len(inline_query.query) == 0:
        for course in courses.values():
            course_name = course['name']
            if len(course_name.split('|')) == 2:
                course_name = ' | '.join(course_name.split('|')[:1] + course_name.split('|')[2:])

            course_id = course['id']
            grades_text = f"[{clear_MD(course_name)}]({clear_MD(f'{url_course}{course_id}')})\n"
            for grade in course['grades'].values():
                name = grade['name']
                percentage = grade['percentage']
                grades_text += f"    {clear_MD(name)}  \-  {clear_MD(percentage)}\n"
            results.append(
                types.InlineQueryResultArticle(
                    id=course_id,
                    title=course_name + ' | Grades',
                    input_message_content=types.InputTextMessageContent(
                            grades_text,
                            parse_mode='MarkdownV2'
                        )
                    )
            )

            assign_text = f"[{clear_MD(course_name)}]({clear_MD(f'{url_course}{course_id}')})\n"
            assign_state = False
            for assign in course['assignments'].values():
                name = assign['name']
                due = assign['due']
                diff_time = get_diff_time(due)
                if diff_time>timedelta(days=0):
                    assign_text += f"\n    [{clear_MD(name)}]({clear_MD(url+assign['id'])})"
                    assign_text += f"\n    {clear_MD(due)}"
                    assign_text += f"\n    Remaining: {clear_MD(diff_time)}"
                    assign_text += '\n'
                    assign_state = True
            if assign_state is False:
                assign_text += f"\n    No such deadlines"
            results.append(
                types.InlineQueryResultArticle(
                    id=str(course_id)+'_assign',
                    title=course_name + ' | Deadlines',
                    input_message_content=types.InputTextMessageContent(
                        assign_text,
                        parse_mode='MarkdownV2'
                    )
                )
            )
    else:
        courses_names = []
        for course in courses.values():
            course_name = course['name']
            courses_names.append(course_name)

        sorted_names = process.extract(inline_query.query, courses_names)

        for course_name, res in sorted_names:
            course = list(course for course in courses.values() if course['name'] == course_name)[0]
            course_id = course['id']
            if len(course_name.split('|')) == 2:
                course_name = ' | '.join(course_name.split('|')[:1] + course_name.split('|')[2:])


            grades_text = f"[{clear_MD(course_name)}]({clear_MD(f'{url_course}{course_id}')})\n"
            for grade in course['grades'].values():
                name = grade['name']
                percentage = grade['percentage']
                grades_text += f"    {clear_MD(name)}  \-  {clear_MD(percentage)}\n"
            results.append(
            types.InlineQueryResultArticle(
                id=course_id,
                title=course_name + ' | Grades',
                input_message_content=types.InputTextMessageContent(
                        grades_text,
                        parse_mode='MarkdownV2'
                    )
                )
            )

            assign_text = f"[{clear_MD(course_name)}]({clear_MD(f'{url_course}{course_id}')})\n"
            assign_state = False
            for assign in course['assignments'].values():
                name = assign['name']
                due = assign['due']
                diff_time = get_diff_time(due)
                if diff_time>timedelta(days=0):
                    assign_text += f"\n    [{clear_MD(name)}]({clear_MD(url+assign['id'])})"
                    assign_text += f"\n    {clear_MD(due)}"
                    assign_text += f"\n    Remaining: {clear_MD(diff_time)}"
                    assign_text += '\n'
                    assign_state = True
            if assign_state:
                results.append(
                    types.InlineQueryResultArticle(
                        id=str(course_id)+'_assign',
                        title=course_name + ' | Deadlines',
                        input_message_content=types.InputTextMessageContent(
                            assign_text,
                            parse_mode='MarkdownV2'
                        )
                    )
                )

    await inline_query.answer(results[:50], is_personal=True, cache_time=None)


async def ignore(inline_query: types.InlineQuery):
    ...


def register_handlers_inline(dp: Dispatcher):
    dp.register_inline_handler(
        show_courses_list,
        IsUser()
    )
    dp.register_inline_handler(
        show_courses_list,
    )
