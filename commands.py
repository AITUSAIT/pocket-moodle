from modules.bot.handlers import default
from modules.bot.handlers import admin

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

