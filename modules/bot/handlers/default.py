from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from config import RATE
from global_vars import dp
from modules.bot.functions.functions import count_active_user, insert_user
from modules.bot.keyboards.default import commands_buttons, main_menu, profile_btn
from modules.bot.keyboards.moodle import add_grades_deadlines_btns, register_moodle_btn
from modules.bot.keyboards.profile import profile_btns
from modules.database import UserDB
from modules.database.models import User
from modules.logger import Logger


@dp.throttled(rate=RATE)
@Logger.log_msg
async def start(message: types.Message, state: FSMContext):
    user_id = int(message.from_user.id)
    user: User = await UserDB.get_user(user_id)

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

        await UserDB.create_user(user_id, None)

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

    await message.answer(text, reply_markup=kb, parse_mode="MarkdownV2")
    await state.finish()
    await insert_user(user_id)


@dp.throttled(rate=RATE)
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

    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await state.finish()


@dp.throttled(rate=RATE)
@Logger.log_msg
async def commands(query: types.CallbackQuery):
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
    await query.message.edit_text(text, reply_markup=main_menu())


@dp.throttled(rate=RATE)
@count_active_user
@Logger.log_msg
async def profile(query: types.CallbackQuery):
    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)

    text = ""

    text += f"User ID: `{user_id}`\n"
    if user.has_api_token():
        text += f"Mail: `{user.mail}`\n"

    await query.message.edit_text(
        text, reply_markup=profile_btns(), parse_mode="MarkdownV2", disable_web_page_preview=True
    )


@dp.throttled(rate=RATE)
@count_active_user
@Logger.log_msg
async def back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)

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

    await query.message.edit_text(text, reply_markup=kb, parse_mode="MarkdownV2")
    await state.finish()


@dp.throttled(rate=RATE)
@count_active_user
async def delete_msg(query: types.CallbackQuery):
    try:
        await query.bot.delete_message(query.message.chat.id, query.message.message_id)
        await query.answer()
    except Exception:
        await query.answer("Error")


def register_handlers_default(dp: Dispatcher):
    dp.register_message_handler(start, commands="start", state="*")
    dp.register_message_handler(help_msg, commands="help", state="*")

    dp.register_callback_query_handler(back_to_main_menu, lambda c: c.data == "main_menu", state="*")
    dp.register_callback_query_handler(commands, lambda c: c.data == "commands", state="*")
    dp.register_callback_query_handler(profile, lambda c: c.data == "profile", state="*")

    dp.register_callback_query_handler(delete_msg, lambda c: c.data == "delete", state="*")
