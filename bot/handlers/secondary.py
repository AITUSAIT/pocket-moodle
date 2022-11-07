import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Set

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from PIL import Image

from bot.functions.functions import get_info_from_forwarded_msg
from bot.functions.rights import is_admin
from bot.keyboards.default import (add_delete_button, commands_buttons,
                                   main_menu)
from bot.keyboards.secondary import finish_adding_photos
from bot.objects.chats import chat_store
from bot.objects.logger import logger, print_msg


class PDF(StatesGroup):
    wait_photos = State()
    wait_process = State()

photo_delivered: Set[int] = set()
photos = {}


async def photos_to_pdf(message: types.Message, state: FSMContext):
    await state.finish()
    text = "Send photos to convert it to PDF"
    await message.reply(text)
    await PDF.wait_photos.set()


async def get_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    if str(message.from_user.id) in photos:
        photos[f'{message.from_user.id}'].append(photo_id)
    else:
        photos[f'{message.from_user.id}'] = [photo_id]
    
    if message.media_group_id is not None:
        if message.from_user.id in photo_delivered:
            return
        photo_delivered.add(message.from_user.id)


        await asyncio.sleep(0.1)
        len_photos = len(photos[f'{message.from_user.id}'])
        text = f"Added photo, total photos - {len_photos}"
        kb = finish_adding_photos()
        await message.reply(text, reply_markup=kb)

        photo_delivered.remove(message.from_user.id)
    else:
        len_photos = len(photos[f'{message.from_user.id}'])
        text = f"Added photo, total photos - {len_photos}"
        kb = finish_adding_photos()
        await message.reply(text, reply_markup=kb)


@print_msg
async def convert_to_pdf(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    text = "Wait, dowloading files..."
    await query.message.edit_text(text, reply_markup=None)

    await PDF.wait_process.set()

    try:
        images = []
        for photo_id in photos[f'{query.from_user.id}']:
            file_path = (await query.bot.get_file(photo_id)).file_path
            await query.bot.download_file(file_path, f"temp/{photo_id}.jpg")
            image = Image.open(f"temp/{photo_id}.jpg")
            image = image.convert('RGB')
            images.append(image)
        
        text = "Wait, converting files..."
        await query.message.edit_text(text, reply_markup=None)

        img = images.pop(0)
        img.save(f"temp/{query.from_user.id}.pdf", save_all=True, append_images=images)
        await query.bot.send_document(query.from_user.id, open(f"temp/{query.from_user.id}.pdf", 'rb'))
    except:
        text = "Error, try again /photos_to_pdf"
        await query.message.edit_text(text, reply_markup=None)
        await state.finish()
    else:
        text = "Ready!"
        await query.message.edit_text(text, reply_markup=main_menu())
        await state.finish()

        for photo_id in photos[f'{query.from_user.id}']:
            os.remove(f'temp/{photo_id}.jpg')
        os.remove(f'temp/{query.from_user.id}.pdf')
        del photos[f'{query.from_user.id}']


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
    dp.register_message_handler(photos_to_pdf, commands="photos_to_pdf", state="*")
    dp.register_message_handler(get_photo, content_types=['photo'], state=PDF.wait_photos)
    dp.register_callback_query_handler(
        convert_to_pdf,
        lambda c: c.data == "finish photos",
        state=PDF.wait_photos
    )

    dp.register_message_handler(last_handler, content_types=['text', 'document', 'photo'], state="*")

    dp.register_errors_handler(all_errors)
