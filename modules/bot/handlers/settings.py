from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from config import dp, rate
from modules.database.models import SettingBot

from ...database import SettingsBotDB
from ...logger import Logger
from ..handlers.moodle import trottle
from ..keyboards.settings import settings_btns


@dp.throttled(rate=rate)
@Logger.log_msg
async def settings(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    settings: SettingBot = await SettingsBotDB.get_settings(user_id)

    await query.message.edit_text('Set settings:', reply_markup=settings_btns(settings))


@dp.throttled(trottle, rate=1)
@Logger.log_msg
async def set_settings(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    state = bool(int(query.data.split()[-1]))
    key = query.data.split()[-2]
    await SettingsBotDB.set_setting(user_id, key, state)

    settings: SettingBot = await SettingsBotDB.get_settings(user_id)

    await query.message.edit_reply_markup(reply_markup=settings_btns(settings))


def register_handlers_settings(dp: Dispatcher):
    dp.register_callback_query_handler(
        settings,
        lambda c: c.data == "settings",
        state="*"
    )
    dp.register_callback_query_handler(
        set_settings,
        lambda c: c.data.split()[0] == "settings",
        lambda c: len(c.data.split()) > 1,
        state="*"
    )