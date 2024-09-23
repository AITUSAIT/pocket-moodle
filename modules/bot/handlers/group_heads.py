from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command

from modules.bot.filters.group_head import IsGroupHead
from modules.bot.keyboards.mailing_settings import settings_btns
from modules.logger import Logger
from modules.pm_api import academic_group
from modules.pm_api.mailing_settings import MailingSettingsAPI
from modules.pm_api.models import MailingSettings


@Logger.log_msg
async def register(message: types.Message):
    group_tg_id = message.chat.id
    group_name = message.chat.full_name
    await academic_group.AcademicGroupAPI().register_group(group_name=group_name, group_tg_id=group_tg_id)


@Logger.log_msg
async def settings(message: types.Message):
    chat_id = message.chat.id
    settings: MailingSettings = await academic_group.AcademicGroupAPI().get_academic_group_settings(group_tg_id=chat_id)

    await message.answer("Set settings:", reply_markup=settings_btns(settings).as_markup())


@Logger.log_msg
async def set_settings(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    chat_id = query.message.chat.id

    settings: MailingSettings = await academic_group.AcademicGroupAPI().get_academic_group_settings(group_tg_id=chat_id)
    key = query.data.split()[-2]
    value = bool(int(query.data.split()[-1]))
    setattr(settings, key, value)
    await MailingSettingsAPI().set_settings(settings.id, settings)

    await query.message.edit_reply_markup(reply_markup=settings_btns(settings).as_markup())


def register_handlers_head_groups(router: Router):
    router.message.register(register, IsGroupHead(), Command("register_mailing"))
    router.message.register(settings, IsGroupHead(), Command("mailing_settings"))

    router.callback_query.register(
        set_settings,
        IsGroupHead(),
        F.func(lambda c: c.data.split()[0] == "mailing_settings"),
        F.func(lambda c: len(c.data.split()) > 1),
    )
