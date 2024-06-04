from aiogram import Dispatcher, F, exceptions, types
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup

import global_vars
from config import TEST
from modules.bot.functions.functions import get_info_from_forwarded_msg, get_info_from_user_id
from modules.bot.functions.rights import IsAdmin, IsManager, IsNotStuff
from modules.bot.keyboards.default import add_delete_button
from modules.logger import Logger


class AdminPromo(StatesGroup):
    wait_days = State()
    wait_usage_count = State()
    wait_usage_settings = State()


async def get(message: types.Message, command: CommandObject):
    if command.args:
        text = await get_info_from_user_id(int(command.args))
        await message.reply(text, parse_mode="MarkdownV2")


async def get_from_msg(message: types.Message):
    text, _, _, _ = await get_info_from_forwarded_msg(message)
    if len(text) > 0:
        await message.reply(text, parse_mode="MarkdownV2", reply_markup=add_delete_button().as_markup())


async def send_msg(message: types.Message, command: CommandObject):
    if command.args:
        chat_id, text = command.args.split(" ", 1)
        text = f"Message from Admin @dake_duck:\n\n{text}"
        try:
            await global_vars.bot.send_message(chat_id, text)
            await message.reply("Success!")
        except exceptions.TelegramRetryAfter as e:
            await message.reply(f"Wait {e} sec")
        except exceptions.TelegramAPIError as e:
            await message.reply(f"{e}")
            Logger.logger.error(f"{chat_id}\n{text}\n{e}\n", exc_info=True)


async def deanon(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.reply_to_message:
        return
    if not message.reply_to_message.from_user:
        return

    text = (
        f"F Name: {message.reply_to_message.from_user.first_name}\n"
        f"L Name: {message.reply_to_message.from_user.last_name}\n"
    )
    text += await get_info_from_user_id(message.reply_to_message.from_user.id)
    await message.reply_to_message.reply(text, parse_mode="MarkdownV2", reply_markup=add_delete_button().as_markup())


async def ignore(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    try:
        await message.delete()
    except Exception:
        ...


def register_handlers_admin(dp: Dispatcher):
    if TEST:
        dp.message.register(ignore, IsNotStuff(), F.text)

    dp.message.register(deanon, IsManager(), F.func(lambda msg: msg.reply_to_message), Command("deanon"))

    dp.message.register(ignore, F.func(lambda msg: int(msg.chat.id) in [-1001768548002] and msg.is_command()))

    dp.message.register(get, IsManager(), Command("get"))
    dp.message.register(
        get_from_msg, IsManager(), F.func(lambda msg: msg.is_forward() and int(msg.chat.id) not in [-1001768548002])
    )
    dp.message.register(send_msg, IsAdmin(), Command("send_msg"))
