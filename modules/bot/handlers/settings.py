from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from config import RATE
from global_vars import dp
from modules.bot.handlers.moodle import trottle
from modules.bot.keyboards.settings import settings_btns
from modules.database import SettingsBotDB
from modules.database.models import SettingBot
from modules.logger import Logger


#FIX: dp.throttled needs to be rewriten as a midleware
@dp.throttled(rate=RATE)
@Logger.log_msg
async def settings(query: types.CallbackQuery):
    user_id = query.from_user.id
    settings: SettingBot = await SettingsBotDB.get_settings(user_id)

    await query.message.edit_text("Set settings:", reply_markup=settings_btns(settings))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
async def set_settings(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    state = bool(int(query.data.split()[-1]))
    key = query.data.split()[-2]
    await SettingsBotDB.set_setting(user_id, key, state)

    settings: SettingBot = await SettingsBotDB.get_settings(user_id)

    await query.message.edit_reply_markup(reply_markup=settings_btns(settings))


def register_handlers_settings(router: Router):
    router.callback_query.register(settings, lambda c: c.data == "settings", state="*")
    router.callback_query.register(
        set_settings, lambda c: c.data.split()[0] == "settings", lambda c: len(c.data.split()) > 1, state="*"
    )
