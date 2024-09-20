from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command

from modules.pm_api import academic_group


async def register(message: types.Message):
    group_tg_id = message.chat.id
    group_name = message.chat.full_name
    await academic_group.AcademicGroupAPI().register_group(group_name=group_name, group_tg_id=group_tg_id)


def register_handlers_groups(router: Router):
    router.message.register(register, Command("register_mailing"))
