import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from fuzzywuzzy import process

from bot.functions.functions import clear_MD
from bot.functions.rights import IsUser
from bot.objects import aioredis


async def show_courses_list(inline_query: types.InlineQuery):
    user_id = inline_query.from_user.id
    courses = json.loads(await aioredis.get_key(user_id, 'courses'))

    results = []
    index = 0
    if len(inline_query.query) == 0:
        for course in courses.values():
            course_name = course['name']
            course_id = course['id']
            text = f"[{clear_MD(course_name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course_id}')})\n"
            for grade in course['grades'].values():
                name = grade['name']
                percentage = grade['percentage']
                text += f"    {clear_MD(name)}  \-  {clear_MD(percentage)}\n"
            results.append(
                types.InlineQueryResultArticle(
                    id=index,
                    title=course_name + ' | Grades',
                    input_message_content=types.InputTextMessageContent(
                            text,
                            parse_mode='MarkdownV2'
                        )
                    )
            )
            index += 1
    else:
        
        courses_names = []
        for course in courses.values():
            course_name = course['name']
            courses_names.append(course_name)

        sorted_names = process.extract(inline_query.query, courses_names)

        for course_name, res in sorted_names:
            course = list(course for course in courses.values() if course['name'] == course_name)[0]
            course_id = course['id']
            text = f"[{clear_MD(course_name)}]({clear_MD(f'https://moodle.astanait.edu.kz/grade/report/user/index.php?id={course_id}')})\n"
            for grade in course['grades'].values():
                name = grade['name']
                percentage = grade['percentage']
                text += f"    {clear_MD(name)}  \-  {clear_MD(percentage)}\n"
            results.append(
            types.InlineQueryResultArticle(
                id=index,
                title=course_name + ' | Grades',
                input_message_content=types.InputTextMessageContent(
                        text,
                        parse_mode='MarkdownV2'
                    )
                )
            )
            index += 1
    await inline_query.answer(results, is_personal=True, cache_time=None)


def register_handlers_inline(dp: Dispatcher):
    dp.register_inline_handler(
        show_courses_list,
        IsUser()
    )
