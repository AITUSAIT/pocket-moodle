from datetime import datetime, timedelta


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)


def get_diff_time(time_str):
    due = datetime.strptime(time_str, '%A, %d %B %Y, %I:%M %p')
    now = datetime.now()
    diff = due-now
    return chop_microseconds(diff)


async def filtered_deadlines_days(day, user):
    text = ''
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    for course in user['courses']:
        state = 1
        course_state = 0
        for deadline in user['courses'][course]['assignments']:
            diff_time = get_diff_time(user['courses'][course]['assignments'][deadline]['due'])
            if diff_time>timedelta(days=0) and diff_time<timedelta(days=day):
                if state:
                    state = 0
                    text += f"[{user['courses'][course]['name']}]({url_course}{user['courses'][course]['id']}):"
                course_state = 1
                text += f"\n    [{user['courses'][course]['assignments'][deadline]['name']}]({url}{user['courses'][course]['assignments'][deadline]['id']})"
                due = user['courses'][course]['assignments'][deadline]['due']
                text += f"\n    {due}"
                text += f"\n    Remaining: {diff_time}"
                text += '\n'
        if course_state:
            text += '\n\n'
    return text


async def filtered_deadlines_course(id, user):
    text = ''
    url = 'https://moodle.astanait.edu.kz/mod/assign/view.php?id='
    url_course = 'https://moodle.astanait.edu.kz/course/view.php?id='
    state = 1
    for deadline in user['courses'][id]['assignments']:
        diff_time = get_diff_time(user['courses'][id]['assignments'][deadline]['due'])
        if diff_time>timedelta(days=0):
            if state:
                state = 0
                text += f"[{user['courses'][id]['name']}]({url_course}{user['courses'][id]['id']}):"
            text += f"\n    [{user['courses'][id]['assignments'][deadline]['name']}]({url}{user['courses'][id]['assignments'][deadline]['id']})"
            due = user['courses'][id]['assignments'][deadline]['due']
            text += f"\n    {due}"
            text += f"\n    Remaining: {diff_time}"
            text += '\n'
    return text


async def get_deadlines_local_by_days(user, day):
    text = await filtered_deadlines_days(day, user)

    return text if len(text.replace('\n', ''))!=0 else 'So far there are no such' 


async def get_deadlines_local_by_course(user, id):
    text = await filtered_deadlines_course(str(id), user)

    return text if len(text.replace('\n', ''))!=0 else 'So far there are no such' 
