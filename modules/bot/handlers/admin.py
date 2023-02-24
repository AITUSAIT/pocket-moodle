import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import exceptions

from ... import database
from ...logger import logger
from ..functions.functions import (clear_MD, delete_msg,
                                   get_info_from_forwarded_msg,
                                   get_info_from_user_id)
from ..functions.rights import IsAdmin
from ..keyboards.default import add_delete_button


class AdminPromo(StatesGroup):
    wait_promocode = State()
    wait_days = State()
    wait_usage_count = State()
    wait_usage_settings = State()


async def get(message: types.Message):
    if len(message.get_args()):
        args = message.get_args()
        text = await get_info_from_user_id(args)
        await message.reply(text, parse_mode='MarkdownV2')


async def get_from_msg(message: types.Message):
    text, user_id, name, mention = await get_info_from_forwarded_msg(message)
    if len(text) > 0:
        await message.reply(text, parse_mode='MarkdownV2', reply_markup=add_delete_button())


async def send_msg(message: types.Message):
    if len(message.get_args()):
        args = message.get_args()
        chat_id, text = args.split(' ', 1)
        text = f"Message from Admin @dake_duck:\n\n{text}"
        try:
            await message.bot.send_message(chat_id, text)
            await message.reply('Success!')
        except exceptions.BotBlocked:
            await message.reply('Bot blocked by user')
            await database.redis.delete(chat_id)
        except exceptions.ChatNotFound:
            await message.reply('Chat not found')
            await database.redis.delete(chat_id)
        except exceptions.RetryAfter as e:
            await message.reply(f'Wait {e} sec')
        except exceptions.UserDeactivated:
            await message.reply('User deactivated')
            await database.redis.delete(chat_id)
        except exceptions.TelegramAPIError:
            await message.reply('Error')
            logger.logger.error(f"{chat_id}\n{text}\n", exc_info=True)


async def create_promocode(message: types.Message, state: FSMContext):
    await AdminPromo.wait_promocode.set()
    msg = await message.answer('Write promo code:')

    async with state.proxy() as data:
        await delete_msg(message)
        data['del_msg'] = msg


async def name_promocode(message: types.Message, state: FSMContext):
    if await database.redis1.hexists('promocodes', message.text):
        msg = await message.answer('Write promo code:')
    else:
        async with state.proxy() as data:
            data['code'] = message.text
        await AdminPromo.wait_days.set()

        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(KeyboardButton('7'), KeyboardButton('30'))
        msg = await message.answer('Write days of promo code:', reply_markup=kb)

    async with state.proxy() as data:
        await delete_msg(message, data['del_msg'])
        data['del_msg'] = msg


async def days_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['days'] = int(message.text)
    await AdminPromo.wait_usage_count.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('-1'), KeyboardButton('1'))
    msg = await message.answer('Write count of usage of promo code:', reply_markup=kb)

    async with state.proxy() as data:
        await delete_msg(message, data['del_msg'])
        data['del_msg'] = msg


async def usage_count_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['count_of_usage'] = int(message.text)
    await AdminPromo.wait_usage_settings.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('all'), KeyboardButton('newbie'))
    msg = await message.answer('Write usage settings of promo code:', reply_markup=kb)

    async with state.proxy() as data:
        await delete_msg(message, data['del_msg'])
        data['del_msg'] = msg


async def push_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['usage_settings'] = message.text
        promocode = {
            'code': data['code'],
            'days': data['days'],
            'count_of_usage': data['count_of_usage'],
            'usage_settings': data['usage_settings'],
            'users': []
        }
    
    await database.redis1.hset('promocodes', data['code'], json.dumps(promocode))
    text = "Promo code has been created\n" \
            f"Code: *`{clear_MD(promocode['code'])}`*"
    await message.answer(text, parse_mode='MarkdownV2')

    async with state.proxy() as data:
        await delete_msg(message, data['del_msg'])

    await state.finish()


async def deanon(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except:
        ...
    text = f"F Name: {message.from_user.first_name}\n" \
            f"L Name: {message.from_user.last_name}\n"
    text += await get_info_from_user_id(message.reply_to_message.from_user.id)
    await message.reply_to_message.reply(text, parse_mode='MarkdownV2')


async def ignore(message: types.Message):
    try:
        await message.delete()
    except:
        ...


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(deanon, IsAdmin(), lambda msg: msg.reply_to_message, commands='deanon', state="*")
    dp.register_message_handler(ignore, lambda msg: int(msg.chat.id) in [-1001768548002] and msg.is_command(), state="*")

    dp.register_message_handler(get, IsAdmin(), commands="get", state="*")
    dp.register_message_handler(get_from_msg, IsAdmin(), lambda msg: msg.is_forward(), state="*")
    dp.register_message_handler(send_msg, IsAdmin(), commands="send_msg", state="*")

    dp.register_message_handler(create_promocode, IsAdmin(), commands="create_promocode", state="*")
    dp.register_message_handler(name_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_promocode)
    dp.register_message_handler(days_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_days)
    dp.register_message_handler(usage_count_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_usage_count)
    dp.register_message_handler(push_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_usage_settings)

