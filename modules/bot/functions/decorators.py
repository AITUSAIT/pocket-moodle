from functools import wraps

from aiogram import types

from modules.bot.keyboards.default import main_menu
from modules.pm_api.api import PocketMoodleAPI


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        arg: types.CallbackQuery | types.Message = args[0]
        if not arg.from_user:
            return

        user_id = arg.from_user.id
        user = await PocketMoodleAPI().get_user(user_id)

        if isinstance(arg, types.Message):
            msg: types.Message = arg
            if not user or not user.has_api_token():
                await msg.reply("First you need to /register", reply_markup=main_menu().as_markup())
                return

            await func(*args, **kwargs)
        elif isinstance(arg, types.CallbackQuery):
            query: types.CallbackQuery = arg
            if not user or not user.has_api_token():
                await query.answer("First you need to /register")
                return

            await func(*args, **kwargs)

    return wrapper
