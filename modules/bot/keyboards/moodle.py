from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.bot.functions.functions import escape_md
from modules.database.models import Course, Deadline


def register_moodle_btn(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Register account", callback_data="register"))

    return kb


def add_grades_deadlines_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Grades", callback_data="get_grades"),
        InlineKeyboardButton(text="Deadlines", callback_data="get_deadlines"),
    )
    kb.row(InlineKeyboardButton(text="Courses' contents", callback_data="courses_contents"))
    kb.row(InlineKeyboardButton(text="Submit Assignment", callback_data="submit_assign"))

    return kb


def grades_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Active courses", callback_data="get_grades active text"),
        InlineKeyboardButton(text="All courses", callback_data="get_grades all text"),
    )
    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def active_grades_btns(
    courses: dict[str, Course], is_active: bool, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for course_id, course in courses.items():
        if not course.active and is_active:
            continue
        btn = InlineKeyboardButton(
            text=course.name,
            callback_data=f"get_grades {'active' if is_active else 'all'} text {course_id}",
        )

        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="get_grades"))

    return kb


def course_back(is_active, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    if is_active:
        main_menu = InlineKeyboardButton(text="Back", callback_data="get_grades active text")
    else:
        main_menu = InlineKeyboardButton(text="Back", callback_data="get_grades all text")
    kb.row(main_menu)

    return kb


def deadlines_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="By active courses", callback_data="get_deadlines active"),
        InlineKeyboardButton(text="By day filter", callback_data="get_deadlines days"),
    )
    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def deadlines_courses_btns(courses: dict[str, Course], kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for course in [course for course in courses.values() if course.active]:
        btn = InlineKeyboardButton(text=course.name, callback_data=f"get_deadlines active {course.course_id}")
        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="get_deadlines"))

    return kb


def deadlines_courses_back_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Back", callback_data="get_deadlines active"))

    return kb


def deadlines_days_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    filters = {
        "<1 day": "get_deadlines days 1",
        "<2 days": "get_deadlines days 2",
        "<5 days": "get_deadlines days 5",
        "<10 days": "get_deadlines days 10",
        "<15 days": "get_deadlines days 15",
    }

    index = 0
    for text, data in filters.items():
        if index % 2 != 1:
            kb.row(InlineKeyboardButton(text=text, callback_data=data))
        else:
            kb.add(InlineKeyboardButton(text=text, callback_data=data))
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="get_deadlines"))

    return kb


def deadlines_days_back_btns(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    main_menu = InlineKeyboardButton(text="Back", callback_data="get_deadlines days")
    kb.add(main_menu)

    return kb


def show_calendar_choices(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    index = 0
    for day in days:
        btn = InlineKeyboardButton(text=f"{day.capitalize()}", callback_data=f"calendar {day}")
        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def show_calendar_day(day_of_week: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Edit events", callback_data=f"calendar {day_of_week} edit"),
        InlineKeyboardButton(text="Back", callback_data="calendar"),
    )

    return kb


def show_calendar_day_for_edit(
    day_of_week: str, days_events: list, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for event in days_events:
        kb.add(InlineKeyboardButton(text=event["name"], callback_data=f"calendar {day_of_week} edit {event['uuid']}"))

    back = InlineKeyboardButton(text="Back", callback_data=f"calendar {day_of_week}")
    new_event = InlineKeyboardButton(text="Create new event", callback_data=f"calendar {day_of_week} new_event")
    delete = InlineKeyboardButton(text="Delete all events", callback_data=f"calendar {day_of_week} delete")
    kb.row(back, new_event)
    kb.row(delete)
    return kb


def show_calendar_event_for_edit(
    day_of_week: str, event_uuid: str, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    change_name = InlineKeyboardButton(
        text="Change name", callback_data=f"calendar {day_of_week} edit {event_uuid} name"
    )
    change_time = InlineKeyboardButton(
        text="Change time", callback_data=f"calendar {day_of_week} edit {event_uuid} timestart"
    )
    change_duration = InlineKeyboardButton(
        text="Change duration", callback_data=f"calendar {day_of_week} edit {event_uuid} duration"
    )
    back = InlineKeyboardButton(text="Back", callback_data=f"calendar {day_of_week} edit")
    delete = InlineKeyboardButton(text="Delete", callback_data=f"calendar {day_of_week} delete {event_uuid}")
    kb.row(change_name, change_time)
    kb.add(change_duration)
    kb.row(back, delete)
    return kb


def confirm_delete_day(day_of_week: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    yes = InlineKeyboardButton(text="Yes", callback_data=f"calendar {day_of_week} delete confirm")
    no = InlineKeyboardButton(text="No", callback_data=f"calendar {day_of_week} edit")
    kb.row(yes, no)
    return kb


def confirm_delete_event(
    day_of_week: str, event_uuid: str, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    yes = InlineKeyboardButton(text="Yes", callback_data=f"calendar {day_of_week} delete {event_uuid} confirm")
    no = InlineKeyboardButton(text="No", callback_data=f"calendar {day_of_week} edit {event_uuid}")
    kb.row(yes, no)
    return kb


def show_courses_for_submit(
    courses: dict[str, Course], kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    index = 0
    for course in courses.values():
        if not course.active:
            continue
        btn = InlineKeyboardButton(text=course.name, callback_data=f"submit_assign {course.course_id}")

        if index % 2 != 1:
            kb.row(btn)
        else:
            kb.add(btn)
        index += 1

    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def show_assigns_for_submit(
    assigns: dict[str, Deadline], course_id: str, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    assign_list = list(assigns.values())
    assign_list.sort(key=lambda x: x.assign_id)
    for assign in assign_list:
        kb.row(InlineKeyboardButton(text=assign.name, callback_data=f"submit_assign {course_id} {assign.assign_id}"))

    kb.row(InlineKeyboardButton(text="Back", callback_data="submit_assign"))

    return kb


def show_assigns_type(course_id: str, assign_id: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="File", callback_data=f"submit_assign {course_id} {assign_id} file"),
        InlineKeyboardButton(text="Text", callback_data=f"submit_assign {course_id} {assign_id} text"),
    )

    kb.row(InlineKeyboardButton(text="Back", callback_data="submit_assign"))

    return kb


def show_assigns_cancel_btn(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Cancel", callback_data="submit_assign cancel"))

    return kb


def show_curriculum_courses(kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="1 Course", callback_data="get_curriculum 1"))
    kb.row(InlineKeyboardButton(text="2 Course", callback_data="get_curriculum 2"))
    kb.row(InlineKeyboardButton(text="3 Course", callback_data="get_curriculum 3"))

    kb.row(InlineKeyboardButton(text="Back", callback_data="main_menu"))

    return kb


def show_curriculum_trimesters(course: str, kb: InlineKeyboardBuilder | None = None) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="1 Trimester", callback_data=f"get_curriculum {course} 1"))
    kb.row(InlineKeyboardButton(text="2 Trimester", callback_data=f"get_curriculum {course} 2"))
    kb.row(InlineKeyboardButton(text="3 Trimester", callback_data=f"get_curriculum {course} 3"))

    kb.row(InlineKeyboardButton(text="Back", callback_data="get_curriculum"))

    return kb


def show_curriculum_components(
    course: str, trimester: str, components: dict, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    for component_id, component in components.items():
        kb.row(
            InlineKeyboardButton(
                text=f"{component['name']} ({component['credits']})",
                callback_data=f"get_curriculum {course} {trimester} {component_id}",
            )
        )

    kb.row(InlineKeyboardButton(text="Back", callback_data=f"get_curriculum {course}"))

    return kb


def back_to_curriculum_trimester(
    course: str, trimester: str, kb: InlineKeyboardBuilder | None = None
) -> InlineKeyboardBuilder:
    if kb is None:
        kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Back", callback_data=f"get_curriculum {course} {trimester}"))

    return kb
