from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from config import RATE
from modules.bot.keyboards.settings import settings_btns
from modules.bot.throttling import rate_limit
from modules.logger import Logger
from modules.pm_api.api import PocketMoodleAPI
from modules.pm_api.models import SettingBot


@rate_limit(limit=RATE)
@Logger.log_msg
async def settings(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id
    settings: SettingBot = await PocketMoodleAPI().get_settings(user_id)

    await query.message.edit_text("Set settings:", reply_markup=settings_btns(settings).as_markup())


@rate_limit(limit=1)
@Logger.log_msg
async def set_settings(query: types.CallbackQuery, state: FSMContext):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id

    settings = await PocketMoodleAPI().get_settings(user_id)
    key = query.data.split()[-2]
    setattr(settings, key, bool(int(query.data.split()[-1])))
    await PocketMoodleAPI().set_settings(user_id, settings)

    await query.message.edit_reply_markup(reply_markup=settings_btns(settings).as_markup())


def register_handlers_settings(router: Router):
    router.callback_query.register(settings, F.func(lambda c: c.data == "settings"))
    router.callback_query.register(
        set_settings, F.func(lambda c: c.data.split()[0] == "settings"), F.func(lambda c: len(c.data.split()) > 1)
    )
