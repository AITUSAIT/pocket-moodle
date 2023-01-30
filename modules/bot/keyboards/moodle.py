from aiogram import types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)


def register_moodle_query(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    purchase_btn = InlineKeyboardButton('🎄Register Moodle account🎄', callback_data=f'register_moodle')
    kb.add(purchase_btn)

    return kb


def add_grades_deadlines_btns(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    submit_assign_btn = InlineKeyboardButton('☃️ Submit Assignment ☃️', callback_data=f'submit_assign')
    grades_btn = InlineKeyboardButton('❄️ Get Grades', callback_data=f'get_grades')
    deadlines_btn = InlineKeyboardButton('Get Deadlines ❄️', callback_data=f'get_deadlines')
    gpa_btn = InlineKeyboardButton('🎄 Get GPA', callback_data=f'get_gpa')
    att_btn = InlineKeyboardButton('Get Attendance 🎄', callback_data=f'get_att')
    calendar_btn = InlineKeyboardButton('☃️ Get Calendar', callback_data=f'calendar')
    curr_btn = InlineKeyboardButton('Get Curriculum ☃️', callback_data=f'get_curriculum')
    kb.add(submit_assign_btn)
    kb.row(grades_btn, deadlines_btn)
    kb.row(gpa_btn, att_btn)
    kb.row(calendar_btn, curr_btn)

    return kb


def grades_btns(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    grades_btn_active = InlineKeyboardButton('Active courses (PDF)', callback_data=f'get_grades active pdf')
    grades_btn_all = InlineKeyboardButton('All courses (PDF)', callback_data=f'get_grades all pdf')
    grades_btn_active_text = InlineKeyboardButton('Active courses (TEXT)', callback_data=f'get_grades active text')
    grades_btn_all_text = InlineKeyboardButton('All courses (TEXT)', callback_data=f'get_grades all text')
    kb.row(grades_btn_active, grades_btn_all)
    kb.row(grades_btn_active_text, grades_btn_all_text)
    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def active_grades_btns(courses, is_active, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, course in courses.items():
        if course['active'] or not is_active:
            if index%2!=1:
                kb.insert(InlineKeyboardButton(course['name'], callback_data=f"get_grades {'active' if is_active else 'all'} text {id}"))
            else:
                if index == 1:
                    kb.insert(InlineKeyboardButton(course['name'], callback_data=f"get_grades {'active' if is_active else 'all'} text {id}"))
                else:
                    kb.add(InlineKeyboardButton(course['name'], callback_data=f"get_grades {'active' if is_active else 'all'} text {id}"))
            index += 1
    main_menu = InlineKeyboardButton('Back', callback_data=f'get_grades')
    kb.add(main_menu)
    
    return kb


def course_back(is_active, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    if is_active:
        main_menu = InlineKeyboardButton('Back', callback_data=f'get_grades active text')
    else:
        main_menu = InlineKeyboardButton('Back', callback_data=f'get_grades all text')
    kb.add(main_menu)
    
    return kb


def deadlines_btns(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton('By active courses', callback_data=f'get_deadlines active'))
    kb.insert(InlineKeyboardButton('By day filter', callback_data=f'get_deadlines days'))
    kb.add(InlineKeyboardButton('Back', callback_data=f'main_menu'))

    return kb


def deadlines_courses_btns(courses, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    courses = list(course for course in courses.values() if course['active'])
    for index in range(0, len(courses), 2):
        if index+1 >= len(courses):
            kb.add(InlineKeyboardButton(courses[index]['name'], callback_data='get_deadlines active ' + courses[index]['id']))
        else:
            kb.row(
                InlineKeyboardButton(courses[index]['name'], callback_data='get_deadlines active ' + courses[index]['id']),
                InlineKeyboardButton(courses[index+1]['name'], callback_data='get_deadlines active ' + courses[index+1]['id'])
            )
        
    main_menu = InlineKeyboardButton('Back', callback_data=f'get_deadlines')
    kb.add(main_menu)
    
    return kb


def deadlines_days_btns(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    filters = {
        '<1 day': 'get_deadlines days 1',
        '<2 days': 'get_deadlines days 2',
        '<5 days': 'get_deadlines days 5',
        '<10 days': 'get_deadlines days 10',
        '<15 days': 'get_deadlines days 15',
        'All': 'get_deadlines days 90',
    }
    
    for index in range(0, len(filters), 2):
        if index+1 >= len(filters):
            kb.add(InlineKeyboardButton(list(filters.keys())[index], callback_data=list(filters.values())[index]))
        else:
            kb.row(
                InlineKeyboardButton(list(filters.keys())[index], callback_data=list(filters.values())[index]),
                InlineKeyboardButton(list(filters.keys())[index+1], callback_data=list(filters.values())[index+1])
            )

    main_menu = InlineKeyboardButton('Back', callback_data=f'get_deadlines')
    kb.add(main_menu)
    
    return kb


def att_btns(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    att_btn_active = InlineKeyboardButton('Only active courses', callback_data=f'get_att active')
    att_btn_total = InlineKeyboardButton('Total', callback_data=f'get_att total')
    kb.row(att_btn_active, att_btn_total)
    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def active_att_btns(courses, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, course in courses.items():
        if course['active']:
            if index%2!=1:
                kb.insert(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
            else:
                if index == 1:
                    kb.insert(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
                else:
                    kb.add(InlineKeyboardButton(course['name'], callback_data=f'get_att active {id}'))
            index += 1
    main_menu = InlineKeyboardButton('Back', callback_data=f'get_att')
    kb.add(main_menu)
    
    return kb


def back_to_get_att(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
        
    att_btn = InlineKeyboardButton('Back', callback_data=f'get_att')
    kb.add(att_btn)
    return kb


def back_to_get_att_active(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
        
    att_btn = InlineKeyboardButton('Back', callback_data=f'get_att active')
    kb.add(att_btn)
    return kb


def show_calendar_choices(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
        
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    index = 1
    for day in days:
        if index%2!=1:
            kb.insert(InlineKeyboardButton(f'{day.capitalize()}', callback_data=f'calendar {day}'))
        else:
            if index == 1:
                kb.insert(InlineKeyboardButton(f'{day.capitalize()}', callback_data=f'calendar {day}'))
            else:
                kb.add(InlineKeyboardButton(f'{day.capitalize()}', callback_data=f'calendar {day}'))
        index += 1

    back = InlineKeyboardButton('Back', callback_data=f'main_menu')
    kb.add(back)
    return kb


def show_calendar_day(day_of_week:str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    edit = InlineKeyboardButton('Edit events', callback_data=f'calendar {day_of_week} edit')
    back = InlineKeyboardButton('Back', callback_data=f'calendar')
    kb.row(back, edit)
    return kb


def show_calendar_day_for_edit(day_of_week:str, days_events: list, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    for event in days_events:
        kb.add(InlineKeyboardButton(event['name'], callback_data=f"calendar {day_of_week} edit {event['uuid']}"))

    back = InlineKeyboardButton('Back', callback_data=f'calendar {day_of_week}')
    new_event = InlineKeyboardButton('Create new event', callback_data=f'calendar {day_of_week} new_event')
    kb.row(back, new_event)
    return kb


def show_calendar_event_for_edit(day_of_week:str, event_uuid: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    change_name = InlineKeyboardButton('Change name', callback_data=f'calendar {day_of_week} edit {event_uuid} name')
    change_time = InlineKeyboardButton('Change time', callback_data=f'calendar {day_of_week} edit {event_uuid} timestart')
    change_duration = InlineKeyboardButton('Change duration', callback_data=f'calendar {day_of_week} edit {event_uuid} duration')
    back = InlineKeyboardButton('Back', callback_data=f'calendar {day_of_week} edit')
    delete = InlineKeyboardButton('Delete', callback_data=f'calendar {day_of_week} delete {event_uuid}')
    kb.row(change_name, change_time)
    kb.add(change_duration)
    kb.row(back, delete)
    return kb


def confirm_delete_event(day_of_week:str, event_uuid: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()

    
    yes = InlineKeyboardButton('Yes', callback_data=f'calendar {day_of_week} delete {event_uuid} confirm')
    no = InlineKeyboardButton('No', callback_data=f"calendar {day_of_week} edit {event_uuid}")
    kb.row(yes, no)
    return kb


def show_courses_for_submit(courses, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    index = 1
    for id, course in courses.items():
        if course['active']:
            if index%2!=1:
                kb.insert(InlineKeyboardButton(course['name'], callback_data=f"submit_assign {id}"))
            else:
                if index == 1:
                    kb.insert(InlineKeyboardButton(course['name'], callback_data=f"submit_assign {id}"))
                else:
                    kb.add(InlineKeyboardButton(course['name'], callback_data=f"submit_assign {id}"))
            index += 1
    main_menu = InlineKeyboardButton('Back', callback_data=f'main_menu')
    kb.add(main_menu)
    
    return kb


def show_assigns_for_submit(assigns, course_id: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    for id, assign in assigns.items():
        kb.add(InlineKeyboardButton(assign['name'], callback_data=f"submit_assign {course_id} {id}"))

    main_menu = InlineKeyboardButton('Back', callback_data=f'submit_assign')
    kb.add(main_menu)
    
    return kb


def show_assigns_type(course_id: str, assign_id: str ,kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    kb.add(InlineKeyboardButton("File", callback_data=f"submit_assign {course_id} {assign_id} file"))
    kb.insert(InlineKeyboardButton("Text", callback_data=f"submit_assign {course_id} {assign_id} text"))

    main_menu = InlineKeyboardButton('Back', callback_data=f'submit_assign')
    kb.add(main_menu)
    
    return kb


def show_assigns_cancel_btn(course_id: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    main_menu = InlineKeyboardButton('Cancel', callback_data=f'submit_assign {course_id}')
    kb.add(main_menu)
    
    return kb


def show_curriculum_courses(kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    kb.add(InlineKeyboardButton('1 Course', callback_data='get_curriculum 1'))
    kb.add(InlineKeyboardButton('2 Course', callback_data='get_curriculum 2'))
    kb.add(InlineKeyboardButton('3 Course', callback_data='get_curriculum 3'))
    
    kb.add(InlineKeyboardButton('Back', callback_data=f'main_menu'))
    return kb


def show_curriculum_trimesters(course: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    kb.add(InlineKeyboardButton('1 Trimester', callback_data=f'get_curriculum {course} 1'))
    kb.add(InlineKeyboardButton('2 Trimester', callback_data=f'get_curriculum {course} 2'))
    kb.add(InlineKeyboardButton('3 Trimester', callback_data=f'get_curriculum {course} 3'))
    
    kb.add(InlineKeyboardButton('Back', callback_data=f'get_curriculum'))
    return kb


def show_curriculum_components(course: str, trimester: str, components: dict, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    for id, component in components.items():
        kb.add(InlineKeyboardButton(f"{component['name']} ({component['credits']})", callback_data=f'get_curriculum {course} {trimester} {id}'))
    
    kb.add(InlineKeyboardButton('Back', callback_data=f'get_curriculum {course}'))
    return kb


def back_to_curriculum_trimester(course: str, trimester: str, kb: types.inline_keyboard = None) -> types.inline_keyboard:
    if kb is None:
        kb = InlineKeyboardMarkup()
    
    kb.add(InlineKeyboardButton('Back', callback_data=f'get_curriculum {course} {trimester}'))
    return kb
    