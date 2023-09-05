from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from config import dp, rate

from ...logger import Logger
from ...database import UserDB
from ...database.models import User
from ..functions.functions import clear_MD, count_active_user, get_diff_time
from ..keyboards.default import commands_buttons, main_menu, profile_btn
from ..keyboards.moodle import add_grades_deadlines_btns, register_moodle_query
from ..keyboards.purchase import profile_btns


@dp.throttled(rate=rate)
@Logger.log_msg
async def start(message: types.Message, state: FSMContext):
    from ...app.api.router import insert_user
    user_id = int(message.from_user.id)
    user: User = await UserDB.get_user(user_id)
    days=2

    if len(message.get_args()) and message.get_args().isnumeric():
        args = message.get_args()
        args_user: User = await UserDB.get_user(args)

        if not user and args_user:
            await UserDB.activate_sub(args_user.user_id, days)
            text_2 = f"You have been added {days} days of subscription!"
            await message.bot.send_message(args_user, text_2, reply_markup=main_menu())
            days = 7

    kb = None
    if not user:
        text = "Hi\! I am Bot for quick and easy work with a Moodle site"
        await message.answer(text, parse_mode='MarkdownV2')

        text = "*With an active subscription✅*:\n" \
                "1\. *Grades* changes notification\n" \
                "2\. *Deadlines* changes notification\n" \
                "3\. Notification of a *deadline* that is about to expire\n" \
                "4\. *Convert* files\n" \
                "5\. *Submit* assignments\n"
        await message.answer(text, parse_mode='MarkdownV2')

        text = "*Without an active subscription❌*:\n" \
                "1\. *Grades*, without notifications\n" \
                "2\. *Deadlines*, without notifications\n"
        await message.answer(text, parse_mode='MarkdownV2')

        await UserDB.create_user(user_id, None)
        await UserDB.activate_sub(user_id, days)

        text = "Steps:\n" \
                "1\. *Register* your Moodle account\n" \
                "2\. *Wait*, the system needs time to get the data\n" \
                "3\. *Enjoy* and have time to close deadlines\n\n" \
                f"I\'m giving you a *{days}\-days trial period*, then you\'ll have to pay for a subscription\n\n"
        kb = register_moodle_query(kb)
    else:
        if not user.has_api_token():
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(kb))
        
        text = "Choose one and click:"

    await message.answer(text, reply_markup=kb, parse_mode='MarkdownV2')
    await state.finish()
    await insert_user(user_id)


@dp.throttled(rate=rate)
@Logger.log_msg
async def help(message: types.Message, state: FSMContext):
    text = "Hi, I'm Pocket Moodle bot!\n" \
            "I was created for receiving notifications about changing grades and deadlines from moodle.astanait.edu.kz\n\n" \
            "All functions are available by subscription.\n\n" \
            "If you have trouble: t.me/dake_duck\n" \
            "If you have question: t.me/pocket_moodle_chat\n" \
            "If you want check news: t.me/pocket_moodle_aitu"
    kb = commands_buttons(main_menu())

    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await state.finish()


@dp.throttled(rate=rate)
@Logger.log_msg
async def commands(query: types.CallbackQuery, state: FSMContext):
    text = "Commands:\n\n" \
            "/start > Start | Info\n" \
            "/help > Help\n" \
            "\n" \
            "/register > Register or Re-register account\n" \
            "/purchase > Purchase subscription\n" \
            "\n" \
            "/submit_assignment > Submit Assignment\n" \
            "/check_finals > Check Finals\n" \
            "\n" \
            "/update > Update info\n" \
            "\n" \
            "/convert > Convert files"
    await query.message.edit_text(text, reply_markup=main_menu())


@dp.throttled(rate=rate)
@count_active_user
@Logger.log_msg
async def profile(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)

    text = ""

    text += f"User ID: `{user_id}`\n"
    if user.has_api_token():
        text += f"Mail: `{user.mail}`\n"
        if user.is_active_sub():
            time = get_diff_time(user.sub_end_date)
            text += f"Subscription is active for *{time}*"
        else:
            text += "Subscription is *not active*"
        text += f"\n\n[Promo\-link]({clear_MD(f'https://t.me/pocket_moodle_aitu_bot?start={user_id}')}) \- share it to get 2days sub for every new user"
    
    await query.message.edit_text(text, reply_markup=profile_btns(), parse_mode='MarkdownV2', disable_web_page_preview=True)


@dp.throttled(rate=rate)
@count_active_user
@Logger.log_msg
async def back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)

    kb = None
    if not user:
        text = "Hi\! I am Bot for quick and easy work with a Moodle site\.\n\n" \
                "1\. *Register* your Moodle account\n" \
                "2\. *Wait* 2 minutes, the system needs time to get the data\n" \
                "3\. *Enjoy* and have time to close deadlines"
        kb = register_moodle_query(commands_buttons(kb))
    else:
        if not user.has_api_token():
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(kb))

        text = "Choose one and click:"

    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')
    await state.finish()


@dp.throttled(rate=rate)
async def delete_msg(query: types.CallbackQuery):
    try:
        await query.bot.delete_message(query.message.chat.id, query.message.message_id)
        await query.answer()
    except Exception as exc:
        # logger.error(exc)
        await query.answer("Error")


def register_handlers_default(dp: Dispatcher):
    dp.register_message_handler(start, commands="start", state="*")
    dp.register_message_handler(help, commands="help", state="*")


    dp.register_callback_query_handler(
        back_to_main_menu,
        lambda c: c.data == "main_menu",
        state="*"
    )
    dp.register_callback_query_handler(
        commands,
        lambda c: c.data == "commands",
        state="*"
    )
    dp.register_callback_query_handler(
        profile,
        lambda c: c.data == "profile",
        state="*"
    )

    dp.register_callback_query_handler(
        delete_msg,
        lambda c: c.data == "delete",
        state="*"
    )
