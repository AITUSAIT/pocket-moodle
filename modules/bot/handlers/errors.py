from aiogram import Dispatcher, F, Router, types

from modules.bot.functions.functions import count_active_user
from modules.bot.keyboards.default import commands_buttons, main_menu
from modules.logger import Logger


@count_active_user
async def last_handler(message: types.Message):
    await message.reply('Try click on "Commands"', reply_markup=commands_buttons(main_menu()).as_markup())


async def all_errors_from_msg(event: types.ErrorEvent, message: types.Message):
    await message.answer("Error, if you have some troubles, /help")
    chat_id = message.chat.id
    text = message.text
    Logger.error(f"{chat_id} {text} {event.exception}", exc_info=True)


async def all_errors_from_callback_query(event: types.ErrorEvent, callback_query: types.CallbackQuery):
    await callback_query.answer("Error, if you have some troubles, /help")
    chat_id = callback_query.from_user.id
    text = callback_query.data
    Logger.error(f"{chat_id} {text} {event.exception}", exc_info=True)


def register_handlers_errors(router: Router):
    router.errors.register(all_errors_from_msg, F.update.message.as_("message"))
    router.errors.register(all_errors_from_callback_query, F.update.callback_query.as_("callback_query"))
