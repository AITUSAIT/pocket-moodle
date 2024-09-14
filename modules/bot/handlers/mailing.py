from typing import List

from aiogram import Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import MAILING_TEST_CHAT_ID
from modules.bot.filters.admin import IsManager
from modules.bot.keyboards.mailing import add_media_btns, approve_btns
from modules.logger import Logger
from modules.mailing_queue import MailingQueue
from modules.mailing_queue.models import MailingModel
from modules.pm_api.academic_group import AcademicGroupAPI


class MailingState(StatesGroup):
    waiting_for_content = State()
    waiting_for_choose_media_or_not = State()
    waiting_for_media = State()
    waiting_for_approve = State()


from modules.mailing_queue import MailingQueue
from modules.mailing_queue.models import MailingModel

MAILING_TEST_CHAT_IDS = (-4570717892, -4586721952, -4501277600, -4586924925, -4540608369)


class MailingState(StatesGroup):
    waiting_for_content = State()
    waiting_for_choose_media_or_not = State()
    waiting_for_media = State()
    waiting_for_approve = State()


@Logger.log_msg
async def start_mailing(message: types.Message, state: FSMContext):
    await message.answer("Send the content for the mailing:")
    await state.set_state(MailingState.waiting_for_content)


@Logger.log_msg
async def handle_content(message: types.Message, state: FSMContext):
    content = message.md_text or message.caption

    if not content:
        await message.answer("There is no content! Try again")
        return

    await state.set_data(
        {
            "content": content,
        }
    )

    await message.reply(
        "Add media?",
        reply_markup=add_media_btns().as_markup(),
    )
    await state.set_state(MailingState.waiting_for_choose_media_or_not)


@Logger.log_msg
async def handle_add_media(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer("Send media:")
    await state.set_state(MailingState.waiting_for_media)


@Logger.log_msg
async def handle_no_media(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    content = data["content"]
    mailing = MailingModel(chat_id=MAILING_TEST_CHAT_ID, content=content, media_type=None, media_id=None)
    await MailingQueue.push(mailing)

    await query.message.answer(
        "Check test channel and Approve!",
        reply_markup=approve_btns().as_markup(),
    )
    await state.set_state(MailingState.waiting_for_approve)


@Logger.log_msg
async def handle_media(message: types.Message, state: FSMContext):
    media: List[types.PhotoSize] | types.PhotoSize | types.Document | None | types.Video = (
        message.photo or message.video or message.document or message.audio
    )

    media_type = None
    media_id = None

    if not media:
        await message.answer("There is no media! Try again")
        return

    if isinstance(media, list):
        media = media[-1]

    if isinstance(media, types.PhotoSize):
        media_type = "photo"
        media_id = media.file_id
    elif isinstance(media, types.Video):
        media_type = "video"
        media_id = media.file_id
    elif isinstance(media, types.Document):
        media_type = "document"
        media_id = media.file_id
    elif isinstance(media, types.Audio):
        media_type = "audio"
        media_id = media.file_id

    data = await state.get_data()
    content = data["content"]
    await state.set_data(
        {
            "content": content,
            "media_type": media_type,
            "media_id": media_id,
        }
    )

    mailing = MailingModel(chat_id=MAILING_TEST_CHAT_ID, content=content, media_type=None, media_id=None)
    await MailingQueue.push(mailing)

    await message.reply(
        "Check test channel and Approve!",
        reply_markup=approve_btns().as_markup(),
    )
    await state.set_state(MailingState.waiting_for_approve)


@Logger.log_msg
async def handle_approve(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    content = data.get("content")
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    if content is None:
        Logger.error("error while trying to get mailing content")
        return

    registered_chat_ids = await AcademicGroupAPI().get_registered_chat_ids()

    for chat_id in registered_chat_ids:
        mailing = MailingModel(chat_id=chat_id, content=content, media_type=media_type, media_id=media_id)
        await MailingQueue.push(mailing)
    await state.clear()
    await query.message.delete()
    if query.message.reply_to_message:
        await query.message.reply_to_message.delete()


@Logger.log_msg
async def handle_decline(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.delete()
    if query.message.reply_to_message:
        await query.message.reply_to_message.delete()


def register_mailing_handlers(dp: Dispatcher):
    dp.message.register(start_mailing, IsManager(), Command("start_mailing"))
    dp.message.register(handle_content, IsManager(), MailingState.waiting_for_content)
    dp.callback_query.register(
        handle_add_media,
        IsManager(),
        F.func(lambda c: c.data.split()[0] == "mailing"),
        F.func(lambda c: c.data.split()[1] == "add_media"),
        MailingState.waiting_for_choose_media_or_not,
    )
    dp.callback_query.register(
        handle_no_media,
        IsManager(),
        F.func(lambda c: c.data.split()[0] == "mailing"),
        F.func(lambda c: c.data.split()[1] == "no_media"),
        MailingState.waiting_for_choose_media_or_not,
    )
    dp.message.register(handle_media, IsManager(), MailingState.waiting_for_media)
    dp.callback_query.register(
        handle_approve,
        IsManager(),
        F.func(lambda c: c.data.split()[0] == "mailing"),
        F.func(lambda c: c.data.split()[1] == "approve"),
        MailingState.waiting_for_approve,
    )
    dp.callback_query.register(
        handle_decline,
        IsManager(),
        F.func(lambda c: c.data.split()[0] == "mailing"),
        F.func(lambda c: c.data.split()[1] == "decline"),
        MailingState.waiting_for_approve,
    )
