from datetime import datetime, timedelta
import json

from aiogram import Dispatcher, types
from aiogram.utils import exceptions

from bot.functions.functions import get_info_from_forwarded_msg, get_info_from_user_id
from bot.functions.rights import is_Admin, is_admin
from bot.keyboards.default import add_delete_button, commands_buttons, main_menu
from bot.objects.chats import chat_store
from bot.objects import aioredis
from bot.objects.logger import logger


@is_Admin
async def send_log(message: types.Message):
    with open('logs.log', 'r') as logs:
        await message.reply_document(logs)


@is_Admin
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

@is_Admin
async def get(message: types.Message):
    if len(message.get_args()):
        args = message.get_args()
        text = await get_info_from_user_id(args)
        await message.reply(text, parse_mode='MarkdownV2')


async def last_handler(message: types.Message):
    try:
        if is_admin(message.from_user.id) and message.is_forward():
            text, user_id, name, mention = await get_info_from_forwarded_msg(message)
            if len(text) > 0:
                await message.reply(text, parse_mode='MarkdownV2', reply_markup=add_delete_button())
        else:
            if message.reply_to_message:
                if message.reply_to_message.forward_from:
                    if (message.chat.id in chat_store or message.reply_to_message.forward_from.id in chat_store) and message.reply_to_message:
                        if message.reply_to_message.is_forward() and is_admin(message.from_user.id):
                            chat_data = chat_store[message.reply_to_message.forward_from.id]
                            chat_id = chat_data['user']
                            from_id = chat_data['admin']
                        else:
                            chat_data = chat_store[message.chat.id]
                            chat_id = chat_data['admin']
                            from_id = chat_data['user']

                        if datetime.now() - chat_data['date'] > timedelta(seconds=1):
                            chat_data['date'] = datetime.now()
                            await message.bot.send_message(chat_id, f"Message from `{from_id}`:", parse_mode='MarkdownV2')
                        await message.forward(chat_id)
            else:
                await message.reply("Try click on \"Commands\"", reply_markup=commands_buttons(main_menu()))
    except Exception as exc:
        logger.error(f"{message.chat.id} - {exc}", exc_info=True)
        await message.reply("Try click on \"Show all features\"", reply_markup=main_menu())


async def all_errors(update: types.Update, error):
    update_json = {}
    update_json = json.loads(update.as_json())
    if 'callback_query' in update_json.keys():
        await update.callback_query.answer('Error, if you have some troubles, /msg_to_admin')
        chat_id = update.callback_query.from_user.id
        text = update.callback_query.data
        logger.error(f"{chat_id} {text} {error}", exc_info=True)
    elif 'message' in update_json.keys():
        await update.message.answer('Error, if you have some troubles, /msg_to_admin')
        chat_id = update.message.from_user.id
        text = update.message.text
        logger.error(f"{chat_id} {text} {error}", exc_info=True)


def register_handlers_secondary(dp: Dispatcher):
    dp.register_message_handler(send_log, commands="get_logfile", state="*")
    dp.register_message_handler(get, commands="get", state="*")
    dp.register_message_handler(send_msg, commands="send_msg", state="*")

    dp.register_message_handler(last_handler, content_types=['text', 'document', 'photo'], state="*")

    dp.register_errors_handler(all_errors)