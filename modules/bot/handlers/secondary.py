import asyncio
from datetime import datetime
import os
from typing import Set

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from PIL import Image

from modules.bot.functions.rights import active_sub_required

from ... import logger as Logger
from ...logger import logger
from ..handlers.default import back_main_menu
from ..keyboards.default import commands_buttons, main_menu
from ..keyboards.secondary import finish_adding_photos


class PDF(StatesGroup):
    wait_photos = State()
    wait_process = State()

photo_delivered: Set[int] = set()
photos = {}


@active_sub_required
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


@Logger.log_msg
@active_sub_required
async def convert_to_pdf(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    await query.answer()

    text = "Wait, dowloading files..."
    await query.message.edit_text(text, reply_markup=None)

    await PDF.wait_process.set()

    try:
        images = []
        for photo_id in photos[str(query.from_user.id)]:
            file_path = (await query.bot.get_file(photo_id)).file_path
            await query.bot.download_file(file_path, f"temp/{photo_id}.jpg")
            images.append(Image.open(f"temp/{photo_id}.jpg").convert('RGB'))
        
        text = "Wait, converting files..."
        await query.message.edit_text(text, reply_markup=None)

        img = images.pop(0)
        date = (datetime.now()).strftime("%Y-%m-%d-%H-%M")
        img.save(f"temp/{query.from_user.id}_{date}.pdf", save_all=True, append_images=images)
        await query.bot.send_document(query.from_user.id, open(f"temp/{query.from_user.id}_{date}.pdf", 'rb'))
    except Exception as exc:
        logger.error(f"{user_id} {exc}")
        text = "Error, try again /photos_to_pdf"
        await query.message.edit_text(text, reply_markup=None)
        await state.finish()
    else:
        text = "Ready!"
        await query.message.edit_text(text, reply_markup=main_menu())
        await state.finish()

        for photo_id in photos[str(query.from_user.id)]:
            os.remove(f'temp/{photo_id}.jpg')
        os.remove(f'temp/{query.from_user.id}_{date}.pdf')
        del photos[str(query.from_user.id)]


@Logger.log_msg
async def cancel_photos(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text("Cancelled", reply_markup=None)
    del photos[f'{query.from_user.id}']
    await state.finish()


async def last_handler(message: types.Message):
    await message.reply("Try click on \"Commands\"", reply_markup=commands_buttons(main_menu()))


async def all_errors(update: types.Update, error):
    if update.callback_query:
        await update.callback_query.answer('Error, if you have some troubles, /help')
        chat_id = update.callback_query.from_user.id
        text = update.callback_query.data
        logger.error(f"{chat_id} {text} {error}", exc_info=True)
    elif update.message:
        await update.message.answer('Error, if you have some troubles, /help')
        chat_id = update.message.from_user.id
        text = update.message.text
        logger.error(f"{chat_id} {text} {error}", exc_info=True)


def register_handlers_secondary(dp: Dispatcher):
    dp.register_message_handler(photos_to_pdf, commands="photos_to_pdf", state="*")
    dp.register_message_handler(get_photo, content_types=['photo'], state=PDF.wait_photos)
    
    dp.register_callback_query_handler(
        cancel_photos,
        lambda c: c.data == "cancel photos",
        state=PDF.wait_photos
    )
    dp.register_callback_query_handler(
        convert_to_pdf,
        lambda c: c.data == "finish photos",
        state=PDF.wait_photos
    )

    # dp.register_message_handler(last_handler, content_types=['text'], state="*")

    dp.register_errors_handler(all_errors)
