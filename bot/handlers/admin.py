import json
from aiogram import Dispatcher, types
from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import exceptions

from bot.functions.functions import get_info_from_user_id
from bot.functions.rights import IsAdmin
from bot.objects import aioredis
from bot.objects.logger import logger


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


async def send_msg(message: types.Message):
    if len(message.get_args()):
        args = message.get_args()
        chat_id, text = args.split(' ', 1)
        text = f"Message from Admin:\n\n{text}"
        try:
            await message.bot.send_message(chat_id, text)
            await message.reply('Success!')
        except exceptions.BotBlocked:
            await message.reply('Bot blocked by user')
            await aioredis.redis.delete(chat_id)
        except exceptions.ChatNotFound:
            await message.reply('Chat not found')
            await aioredis.redis.delete(chat_id)
        except exceptions.RetryAfter as e:
            await message.reply(f'Wait {e} sec')
        except exceptions.UserDeactivated:
            await message.reply('User deactivated')
            await aioredis.redis.delete(chat_id)
        except exceptions.TelegramAPIError:
            await message.reply('Error')
            logger.error(f"{chat_id}\n{text}\n", exc_info=True)


async def create_promocode(message: types.Message):
    await AdminPromo.wait_promocode.set()
    await message.reply('Write promo code:')


async def name_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code'] = message.text
    await AdminPromo.wait_days.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('7'), KeyboardButton('30'))
    await message.reply('Write days of promo code:', reply_markup=kb)


async def days_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['days'] = int(message.text)
    await AdminPromo.wait_usage_count.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('-1'), KeyboardButton('1'))
    await message.reply('Write count of usage of promo code:', reply_markup=kb)


async def usage_count_promocode(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['count_of_usage'] = int(message.text)
    await AdminPromo.wait_usage_settings.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton('all'), KeyboardButton('newbie'))
    await message.reply('Write usage settings of promo code:', reply_markup=kb)


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
    
    await aioredis.redis1.hset('promocodes', data['code'], json.dumps(promocode))
    await message.reply('Promo code has been created')
    await state.finish()


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(get, IsAdmin(), commands="get", state="*")
    dp.register_message_handler(send_msg, IsAdmin(), commands="send_msg", state="*")

    dp.register_message_handler(create_promocode, IsAdmin(), commands="create_promocode", state="*")
    dp.register_message_handler(name_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_promocode)
    dp.register_message_handler(days_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_days)
    dp.register_message_handler(usage_count_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_usage_count)
    dp.register_message_handler(push_promocode, IsAdmin(), content_types=['text'], state=AdminPromo.wait_usage_settings)
