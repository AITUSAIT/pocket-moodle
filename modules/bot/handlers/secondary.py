import asyncio
import typing
from datetime import datetime
from typing import List, Set

import file_converter
from aiogram import Dispatcher, F, types
from aiogram.enums.chat_action import ChatAction
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.media_group import MediaGroupBuilder
from file_converter import JPGs, PNGs

import global_vars
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
files: dict[str, list[str]] = {}

same_formats = {
    "jpg": ["jpeg", "jpg"],
    "jpeg": ["jpeg", "jpg"],
}

docs = ("docx", "pdf")


@Logger.log_msg
@count_active_user
@login_required
async def convert_choose_format(query: types.CallbackQuery | types.Message, state: FSMContext):
    if not query.from_user:
        return

    await state.clear()
    text = "Choose original format:"

    if isinstance(query, types.CallbackQuery):
        if not query.message:
            return
        if isinstance(query.message, types.InaccessibleMessage):
            return
        if not query.data:
            return

        await query.message.edit_text(text, reply_markup=list_formats_kb(file_converter.__all__).as_markup())

    elif isinstance(query, types.Message):
        message = query

        await message.reply(text, reply_markup=list_formats_kb(file_converter.__all__).as_markup())

    if str(query.from_user.id) in files:
        del files[str(query.from_user.id)]


@Logger.log_msg
@login_required
async def convert_choose_dest_format(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    from_format = query.data.split(" ")[1]
    file_format = file_converter.define_class_for_format(from_format)
    text = "Choose destination format:"
    if not file_format:
        return

    await query.message.edit_text(
        text, reply_markup=list_dest_formats_kb(from_format, file_format.can_converts_to).as_markup()
    )


@Logger.log_msg
@login_required
async def convert_wait_files(query: types.CallbackQuery, state: FSMContext):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    from_format = query.data.split(" ")[1]
    dest_format = query.data.split(" ")[2]
    text = f"Now send me `{from_format.upper()}` files and i will convert it to `{dest_format.upper()}`"

    msg = await query.message.edit_text(text, reply_markup=cancel_convert_kb().as_markup(), parse_mode="MarkdownV2")
    await state.set_state(CONVERT.wait_files)
    data = await state.get_data()
    data["format"] = from_format
    data["dest_format"] = dest_format
    data["msg_del"] = msg
    await state.set_data(data)


async def get_files(message: types.Message, state: FSMContext):
    if not message.from_user:
        return
    if not message.document:
        return
    if not message.document.file_name:
        return

    data = await state.get_data()
    await delete_msg(data["msg_del"])
    from_format = data["format"]
    dest_format = data["dest_format"]

    from_file_format = file_converter.define_class_for_format(from_format)
    if not from_file_format:
        return

    actual_file_format = message.document.file_name.split(".")[-1].lower()
    if from_file_format.format != actual_file_format and actual_file_format not in same_formats.get(
        actual_file_format, []
    ):
        text = (
            f"Warning\!\n\nYou should upload `{from_file_format.format.upper()}` files to convert it to `{dest_format}`"
        )
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

    msg = await message.reply(text, reply_markup=finish_adding_files_kb().as_markup(), parse_mode="MarkdownV2")
    data = await state.get_data()
    data["msg_del"] = msg
    await state.set_data(data)


@Logger.log_msg
@count_active_user
@login_required
async def convert(query: types.CallbackQuery, state: FSMContext):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id
    data = await state.get_data()
    from_format = data["format"]
    dest_format = data["dest_format"]
    file_format = file_converter.define_class_for_format(from_format)

    if not file_format:
        return

    if files.get(str(query.from_user.id), []) == []:
        await query.answer("You need to upload files before this action!")
        return
    await query.answer()

    text = "Wait, dowloading files..."
    await query.message.edit_text(text, reply_markup=None)

    await state.set_state(CONVERT.wait_process)

    try:
        result_files: List[typing.BinaryIO] = []
        for file_id in files.get(str(query.from_user.id), []):
            file_path = (await global_vars.bot.get_file(file_id)).file_path
            if not file_path:
                continue

            file_bytes = await global_vars.bot.download_file(file_path=file_path, seek=True)
            if not file_bytes:
                return
            result_files.append(file_bytes)

        text = "Wait, converting files..."
        await query.message.edit_text(text, reply_markup=None)

        date = (datetime.now()).strftime("%Y-%m-%d-%H-%M")

        if file_format in [JPGs, PNGs]:
            file = file_format(result_files)
            result_files = [file.convert_to(dest_format)]
        elif file_format is not None:
            formated_files = [file_format(result_file) for result_file in result_files]
            result_files = [formated_file.convert_to(dest_format) for formated_file in formated_files]

        for file in result_files:
            file.seek(0)

        await global_vars.bot.send_chat_action(query.message.chat.id, ChatAction.UPLOAD_DOCUMENT)

        chunks = [result_files[i : i + 10] for i in range(0, len(result_files), 10)]

        for chunk in chunks:
            media_group = MediaGroupBuilder()

            for i, file in enumerate(chunk):
                if dest_format.lower() in docs:
                    media_group.add_document(
                        media=types.BufferedInputFile(
                            file=file.read(), filename=f"{user_id}_{date}_{i}.{dest_format.lower()}"
                        )
                    )
                else:
                    media_group.add_photo(
                        media=types.BufferedInputFile(
                            file=file.read(), filename=f"{user_id}_{date}_{i}.{dest_format.lower()}"
                        )
                    )

            await global_vars.bot.send_media_group(chat_id=user_id, media=media_group.build())

    except Exception as exc:
        Logger.error(f"{user_id} {str(exc)}", exc_info=True)
        text = "Error, try again /convert"
        await query.message.edit_text(text, reply_markup=None)
        await state.clear()
    else:
        text = "Ready!"
        await query.message.edit_text(text, reply_markup=main_menu().as_markup())
        await state.clear()

    if str(query.from_user.id) in files:
        del files[str(query.from_user.id)]


@Logger.log_msg
async def cancel_convert(query: types.CallbackQuery, state: FSMContext):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.message.reply_to_message:
        return
    if not query.data:
        return

    await query.answer("Cancelled!")
    await delete_msg(query.message, query.message.reply_to_message)
    if str(query.from_user.id) in files:
        del files[f"{query.from_user.id}"]
    await state.clear()


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


def register_handlers_secondary(dp: Dispatcher):
    dp.message.register(convert_choose_format, Command("convert"))
    dp.callback_query.register(
        convert_choose_format,
        F.func(lambda c: c.data == "convert"),
    )

    dp.callback_query.register(cancel_convert, F.func(lambda c: c.data == "convert_cancel"))

    dp.callback_query.register(
        convert_choose_dest_format,
        F.func(lambda c: c.data.split(" ")[0] == "convert"),
        F.func(lambda c: len(c.data.split(" ")) == 2),
    )
    dp.callback_query.register(
        convert_wait_files,
        F.func(lambda c: c.data.split(" ")[0] == "convert"),
        F.func(lambda c: len(c.data.split(" ")) == 3),
    )

    dp.message.register(get_files, F.document, CONVERT.wait_files)

    dp.callback_query.register(convert, F.func(lambda c: c.data == "convert_finish"), CONVERT.wait_files)

    dp.message.register(last_handler, F.text)

    dp.errors.register(all_errors_from_msg, F.update.message.as_("message"))
    dp.errors.register(all_errors_from_callback_query, F.update.callback_query.as_("callback_query"))
