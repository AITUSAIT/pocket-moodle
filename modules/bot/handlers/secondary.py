import asyncio
import io
from datetime import datetime
from typing import Set

import file_converter
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from file_converter import JPGs, PNGs

from modules.bot.functions.functions import count_active_user, delete_msg
from modules.bot.functions.rights import login_required
from modules.bot.keyboards.default import commands_buttons, main_menu
from modules.bot.keyboards.secondary import (
    cancel_convert_kb,
    finish_adding_files_kb,
    list_dest_formats_kb,
    list_formats_kb,
)
from modules.logger import Logger


class CONVERT(StatesGroup):
    wait_files = State()
    wait_process = State()


files_delivered: Set[int] = set()
files = {}

same_formats = {
    "jpg": ["jpeg", "jpg"],
    "jpeg": ["jpeg", "jpg"],
}


@Logger.log_msg
@count_active_user
@login_required
async def convert_choose_format(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = "Choose original format:"

    if query.__class__ is types.CallbackQuery:
        await query.message.edit_text(text, reply_markup=list_formats_kb(file_converter.__all__))

    elif query.__class__ is types.Message:
        message: types.Message = query

        await message.reply(text, reply_markup=list_formats_kb(file_converter.__all__))

    if str(query.from_user.id) in files:
        del files[str(query.from_user.id)]


@Logger.log_msg
@login_required
async def convert_choose_dest_format(query: types.CallbackQuery):
    from_format = query.data.split(" ")[1]
    file_format = file_converter.define_class_for_format(from_format)
    text = "Choose destination format:"

    await query.message.edit_text(text, reply_markup=list_dest_formats_kb(from_format, file_format.can_converts_to))


@Logger.log_msg
@login_required
async def convert_wait_files(query: types.CallbackQuery, state: FSMContext):
    from_format = query.data.split(" ")[1]
    dest_format = query.data.split(" ")[2]
    text = f"Now send me `{from_format.upper()}` files and i will convert it to `{dest_format.upper()}`"

    msg = await query.message.edit_text(text, reply_markup=cancel_convert_kb(), parse_mode="MarkdownV2")
    await CONVERT.wait_files.set()
    async with state.proxy() as data:
        data["format"] = from_format
        data["dest_format"] = dest_format
        data["msg_del"] = msg


async def get_files(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await delete_msg(data["msg_del"])
        from_format = data["format"]
        dest_format = data["dest_format"]

    file_format = file_converter.define_class_for_format(from_format)

    file_format = message.document.file_name.split(".")[-1].lower()
    if file_format.format != file_format and file_format not in same_formats.get(file_format.format, []):
        text = f"Warning\!\n\nYou should upload `{file_format.format.upper()}` files to convert it to `{dest_format}`"
    else:
        file_id = message.document.file_id
        if str(message.from_user.id) in files:
            files[f"{message.from_user.id}"].append(file_id)
        else:
            files[f"{message.from_user.id}"] = [file_id]

        if message.media_group_id is not None:
            if message.from_user.id in files_delivered:
                return
            files_delivered.add(message.from_user.id)

            await asyncio.sleep(0.2)
            len_files = len(files[f"{message.from_user.id}"])
            text = f"Added files, total files \- {len_files}"
            files_delivered.remove(message.from_user.id)
        else:
            len_files = len(files[f"{message.from_user.id}"])
            text = f"Added file, total files \- {len_files}"

    msg = await message.reply(text, reply_markup=finish_adding_files_kb(), parse_mode="MarkdownV2")
    async with state.proxy() as data:
        data["msg_del"] = msg


@Logger.log_msg
@count_active_user
@login_required
async def convert(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    async with state.proxy() as data:
        from_format = data["format"]
        dest_format = data["dest_format"]
    file_format = file_converter.define_class_for_format(from_format)

    if files.get(str(query.from_user.id), []) == []:
        await query.answer("You need to upload files before this action!")
        return
    await query.answer()

    text = "Wait, dowloading files..."
    await query.message.edit_text(text, reply_markup=None)

    await CONVERT.wait_process.set()

    try:
        result_files: list[io.BytesIO] = []
        for file_id in files.get(str(query.from_user.id), []):
            file_path = (await query.bot.get_file(file_id)).file_path
            result_files.append(await query.bot.download_file(file_path))

        text = "Wait, converting files..."
        await query.message.edit_text(text, reply_markup=None)

        date = (datetime.now()).strftime("%Y-%m-%d-%H-%M")

        if file_format in [JPGs, PNGs]:
            file = file_format(result_files)
            result_files = [file.convert_to(dest_format)]
        else:
            result_files = [file_format(_) for _ in result_files]
            result_files = [_.convert_to(dest_format) for _ in result_files]

        for _ in result_files:
            _.seek(0)

        await query.bot.send_chat_action(query.message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)

        chunks = [result_files[i : i + 10] for i in range(0, len(result_files), 10)]

        for chunk in chunks:
            media_group = [
                types.InputMediaDocument(
                    media=types.InputFile(file, filename=f"{user_id}_{date}_{i}.{dest_format.lower()}")
                )
                for i, file in enumerate(chunk)
            ]
            await query.bot.send_media_group(chat_id=user_id, media=media_group)

    except Exception as exc:
        Logger.error(f"{user_id} {str(exc)}", exc_info=True)
        text = "Error, try again /convert"
        await query.message.edit_text(text, reply_markup=None)
        await state.finish()
    else:
        text = "Ready!"
        await query.message.edit_text(text, reply_markup=main_menu())
        await state.finish()

    if str(query.from_user.id) in files:
        del files[str(query.from_user.id)]


@Logger.log_msg
async def cancel_convert(query: types.CallbackQuery, state: FSMContext):
    await query.answer("Cancelled!")
    await delete_msg(query.message, query.message.reply_to_message)
    if str(query.from_user.id) in files:
        del files[f"{query.from_user.id}"]
    await state.finish()


@count_active_user
async def last_handler(message: types.Message):
    await message.reply('Try click on "Commands"', reply_markup=commands_buttons(main_menu()))


async def all_errors(update: types.Update, error):
    if update.callback_query:
        await update.callback_query.answer("Error, if you have some troubles, /help")
        chat_id = update.callback_query.from_user.id
        text = update.callback_query.data
        Logger.error(f"{chat_id} {text} {error}", exc_info=True)
    elif update.message:
        await update.message.answer("Error, if you have some troubles, /help")
        chat_id = update.message.from_user.id
        text = update.message.text
        Logger.error(f"{chat_id} {text} {error}", exc_info=True)


def register_handlers_secondary(dp: Dispatcher):
    dp.register_message_handler(convert_choose_format, commands="convert", state="*")
    dp.register_callback_query_handler(
        convert_choose_format,
        lambda c: c.data == "convert",
    )

    dp.register_callback_query_handler(cancel_convert, lambda c: c.data == "convert_cancel", state="*")

    dp.register_callback_query_handler(
        convert_choose_dest_format,
        lambda c: c.data.split(" ")[0] == "convert",
        lambda c: len(c.data.split(" ")) == 2,
    )
    dp.register_callback_query_handler(
        convert_wait_files,
        lambda c: c.data.split(" ")[0] == "convert",
        lambda c: len(c.data.split(" ")) == 3,
    )

    dp.register_message_handler(get_files, content_types=["document"], state=CONVERT.wait_files)

    dp.register_callback_query_handler(convert, lambda c: c.data == "convert_finish", state=CONVERT.wait_files)

    # dp.register_message_handler(last_handler, content_types=['text'], state="*")

    dp.register_errors_handler(all_errors)
