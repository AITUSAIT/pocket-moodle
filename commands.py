from modules.bot.handlers import default
from modules.bot.handlers import admin
from modules.bot.handlers import moodle

default_commands = {
    '/start': default.start,
    '/help': default.help,
    '/info': default.info,

    'q back_main_menu': default.back_main_menu,
    'q commands': default.commands,
    'q sleep': default.sleep,
    'q awake': default.sleep,
    'q delete': default.delete_msg,
}

admin_commands = {
    '/get {id}': admin.get,
    '{msg}': admin.get_from_msg,
    '/send_msg {id}': admin.send_msg,

    '/create_promocode': admin.create_promocode,
    '{text}': admin.name_promocode,
    '{text}': admin.days_promocode,
    '{text}': admin.usage_count_promocode,
    '{text}': admin.push_promocode,
}

moodle_commands = {
    '/register_moodle': moodle.register_moodle,
    '{text}': moodle.wait_barcode,
    '{text}': moodle.wait_password,


    '/get_grades': moodle.get_grades,
    'q get_grades': moodle.get_grades,

    'q get_grades {is_active} pdf': moodle.get_grades_pdf,

    'q get_grades {is_active} text': moodle.get_grades_choose_course_text,
    'q get_grades {is_active} text {id}': moodle.get_grades_course_text,


    '/get_deadlines': moodle.get_deadlines,
    'q get_deadlines': moodle.get_deadlines,

    'q get_deadlines active': moodle.get_deadlines_choose_courses,
    'q get_deadlines active {id}': moodle.get_deadlines_course,

    'q get_deadlines days': moodle.get_deadlines_choose_days,
    'q get_deadlines days {id}': moodle.get_deadlines_days,


    'q get_gpa': moodle.get_gpa,


    'q get_att': moodle.get_att_choose,
    'q get_att {is_active}': moodle.get_att,
    'q get_att active {id}': moodle.get_att_course,


    'q get_calendar': moodle.get_calendar,
    'q get_calendar this_week': moodle.get_calendar_this_week,
    'q get_calendar {year} {month} {day}': moodle.get_calendar_day,


    'q get_curriculum': moodle.get_curriculum,
    'q get_curriculum {course}': moodle.get_curriculum_trimesters,
    'q get_curriculum {course} {trimester}': moodle.get_curriculum_components,
    'q get_curriculum {course} {trimester} {id}': moodle.get_curriculum_show_component,
}

purchase_commands = {}
