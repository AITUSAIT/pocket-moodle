from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

import global_vars
from config import RATE
from modules.bot.functions.decorators import login_required
from modules.bot.functions.functions import count_active_user, insert_user
from modules.bot.keyboards.default import commands_buttons, main_menu, profile_btn
from modules.bot.keyboards.moodle import add_grades_deadlines_btns, register_moodle_btn
from modules.bot.keyboards.profile import profile_btns
from modules.bot.throttling import rate_limit
from modules.database import UserDB
from modules.logger import Logger


@rate_limit(RATE)
@Logger.log_msg
@login_required
async def activate(message: types.Message): ...


@rate_limit(RATE)
@Logger.log_msg
@login_required
async def mailing_settings(message: types.Message): ...


def register_group_headas_handlers(router: Router):
    router.message.register(activate, Command("/register_group"))
    router.message.register(mailing_settings, Command("/mailing_settings"))
