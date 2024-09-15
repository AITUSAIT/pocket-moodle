from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

import global_vars
from config import RATE
from modules.bot.functions.functions import count_active_user, insert_user
from modules.bot.keyboards.default import commands_buttons, main_menu, profile_btn
from modules.bot.keyboards.moodle import add_grades_deadlines_btns, register_moodle_btn
from modules.bot.keyboards.profile import profile_btns
from modules.bot.throttling import rate_limit
from modules.logger import Logger
from modules.pm_api.api import PocketMoodleAPI


@rate_limit(limit=RATE)
@Logger.log_msg
async def start(message: types.Message, state: FSMContext):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)

    kb = None
    if not user:
        text = "Hi\! I am Bot for quick and easy work with a Moodle site"
        await message.answer(text, parse_mode="MarkdownV2")

        text = (
            "*What I can do for you*:\n"
            "1\. *Grades* changes notification\n"
            "2\. *Deadlines* changes notification\n"
            "3\. Notification of a *deadline* that is about to expire\n"
            "4\. *Convert* files\n"
            "5\. *Submit* assignments\n\n"
            "All functions are *FREE*"
        )
        await message.answer(text, parse_mode="MarkdownV2")

        await PocketMoodleAPI().create_user(user_id)

        text = (
            "Steps:\n"
            "1\. *Register* your Moodle account\n"
            "2\. *Wait*, the system needs time to get the data\n"
            "3\. *Enjoy* and have time to close deadlines"
        )
        kb = register_moodle_btn(kb)
    else:
        if not user.has_api_token():
            kb = register_moodle_btn(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(kb))

        text = "Choose one and click:"

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="MarkdownV2")
    await state.clear()
    await PocketMoodleAPI().insert_user(user_id)


@rate_limit(limit=RATE)
@Logger.log_msg
async def help_msg(message: types.Message, state: FSMContext):
    text = (
        "Hi, I'm Pocket Moodle bot!\n"
        "I was created for receiving notifications about changing grades and deadlines from moodle.astanait.edu.kz\n\n"
        "All functions are *FREE*.\n\n"
        "If you have trouble: t.me/dake_duck\n"
        "If you have question: t.me/pocket_moodle_chat\n"
        "If you want check news: t.me/pocket_moodle_aitu"
    )
    kb = commands_buttons(main_menu())

    await message.answer(text, reply_markup=kb.as_markup(), disable_web_page_preview=True)
    await state.clear()


@rate_limit(limit=RATE)
@Logger.log_msg
async def commands(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    text = (
        "Commands:\n\n"
        "/start > Start | Info\n"
        "/help > Help\n"
        "\n"
        "/register > Register or Re-register account\n"
        "\n"
        "/submit_assignment > Submit Assignment\n"
        "/check_finals > Check Finals\n"
        "\n"
        "/update > Update info\n"
        "\n"
        "/convert > Convert files"
    )
    await query.message.edit_text(text, reply_markup=main_menu().as_markup())


@rate_limit(limit=RATE)
@count_active_user
@Logger.log_msg
async def profile(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)
    if not user:
        return

    text = ""

    text += f"User ID: `{user_id}`\n"
    if user.has_api_token():
        text += f"Mail: `{user.mail}`\n"

    await query.message.edit_text(
        text, reply_markup=profile_btns().as_markup(), parse_mode="MarkdownV2", disable_web_page_preview=True
    )


@rate_limit(limit=RATE)
@count_active_user
@Logger.log_msg
async def back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    user_id = query.from_user.id
    user = await PocketMoodleAPI().get_user(user_id)

    kb = None
    if not user:
        text = (
            "Hi\! I am Bot for quick and easy work with a Moodle site\.\n\n"
            "1\. *Register* your Moodle account\n"
            "2\. *Wait* 2 minutes, the system needs time to get the data\n"
            "3\. *Enjoy* and have time to close deadlines"
        )
        kb = register_moodle_btn(commands_buttons(kb))
    else:
        if not user.has_api_token():
            kb = register_moodle_btn(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(kb))

        text = "Choose one and click:"

    await query.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="MarkdownV2")
    await state.clear()


@rate_limit(limit=RATE)
@count_active_user
async def delete_msg(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    try:
        await global_vars.bot.delete_message(query.message.chat.id, query.message.message_id)
        await query.answer()
    except Exception:
        await query.answer("Error")


def register_handlers_default(router: Router):
    router.message.register(start, Command("start"))
    router.message.register(help_msg, Command("help"))

    router.callback_query.register(back_to_main_menu, F.func(lambda c: c.data == "main_menu"))
    router.callback_query.register(commands, F.func(lambda c: c.data == "commands"))
    router.callback_query.register(profile, F.func(lambda c: c.data == "profile"))

    router.callback_query.register(delete_msg, F.func(lambda c: c.data == "delete"))
