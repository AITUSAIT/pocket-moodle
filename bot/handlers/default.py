import random
from datetime import datetime

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.functions.functions import get_diff_time
from bot.functions.rights import admin_list
from bot.objects.logger import logger, print_msg
from bot.keyboards.default import add_delete_button, commands_buttons, main_menu, profile_btn, sub_menu
from bot.keyboards.moodle import (add_grades_deadlines_btns,
                                  register_moodle_query)
from bot.keyboards.purchase import start_buttons
from bot.objects import aioredis
from bot.objects.chats import chat_store


@print_msg
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if len(message.get_args()):
        args = message.get_args()
        if args == 'me':
            text = f"`{message.from_user.id}`"
            await message.reply(text, parse_mode='MarkdownV2')

    kb = None
    if not await aioredis.if_user(user_id):
        text = "Hi, I\'m Pocket Moodle bot\!\n" \
                "I was created for receiving notifications about changing grades and deadlines from moodle\.astanait\.edu\.kz\n\n" \
                "Pocket Moodle \- a system that saves your barcode and password \(encrypted\)" \
                " from the Moodle account in order to receive information about your grades " \
                "through it, store and provide it in a form convenient for you\.\n\nThis system is" \
                " based on a commercial basis, that is, the use of the bot is paid, but there is a" \
                " demo for familiarization\. Collecting, storing, and sending information requires large capacities, so the bot is paid, and the cost may vary from the cost of providing the system\n\n" \
                "The bot is not official and is not associated with the " \
                "administration of AITU\n\n" \
                "By continuing to use Pocket Moodle, you agree to the /PrivacyPolicy" \
                " and /UserAgreement"
        await message.answer(text, reply_markup=add_delete_button(), parse_mode='MarkdownV2', disable_web_page_preview=True)
        
        text = "*Instructions for the bot*\n\n" \
                "First you need to /purchase a Subscription or activate " \
                "a /demo for 1 month\. \n\nThen you will be asked to /register\_moodle " \
                "account \(save it in the database\), if everything " \
                "went well, the system will save your data from the site and you" \
                " will be able to quickly receive your grades and deadlines, as " \
                "well as their changes\."
        await message.answer(text, reply_markup=add_delete_button(), parse_mode='MarkdownV2')

        text = "All functions and channel are available by subscription\.\n" \
                "Also *I\'m giving you 1 month of free use*, it will be enough to figure it out"
        kb = start_buttons(kb)
    else:
        if not await aioredis.is_activaited_demo(user_id):
            kb = start_buttons(kb)
        else:
            kb = commands_buttons(kb)
        if not await aioredis.is_registered_moodle(user_id):
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(sub_menu(kb)))
        
        text = "Choose one and click:"

    await message.answer(text, reply_markup=kb, parse_mode='MarkdownV2')
    await state.finish()


@print_msg
async def help(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    kb = None
    if not await aioredis.if_user(user_id):
        text = "Hi, I'm Pocket Moodle bot!\n" \
                "I was created for receiving notifications about changing grades and deadlines from moodle.astanait.edu.kz\n\n" \
                "All functions and channel are available by subscription. Also I'm giving you 1 month of free use, it will be enough to figure it out"
        kb = start_buttons(kb)
    else:
        if not await aioredis.is_activaited_demo(user_id):
            kb = start_buttons(kb)
        else:
            kb = commands_buttons(kb)
        if not await aioredis.is_registered_moodle(user_id):
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(kb)
        text = "Choose one and click:"

    await message.answer(text, reply_markup=kb)
    await state.finish()


@print_msg
async def msg_to_admin(message: types.Message, state: FSMContext):
    admin_id = random.choice(admin_list)
    msg = await message.reply(f"Reply this message to send message to Admin, or @dake\_duck if you have *Privacy settings*",
                        parse_mode='MarkdownV2')
    new_chat = {
        'admin': admin_id,
        'user': msg.reply_to_message.chat.id,
        'date': datetime.now()
    }
    
    chat_store[message.chat.id] = new_chat


@print_msg
async def commands(query: types.CallbackQuery, state: FSMContext):
    text = "Commands:\n\n" \
            "/start > Start | Info\n" \
            "/msg_to_admin > Write to Admin\n" \
            "/demo > Activate 1 month demo\n\n" \
            "/register_moodle > Register or Re-register Moodle account\n" \
            "/get_grades > Get grades\n" \
            "/get_deadlines > Get deadlines\n" \
            "/get_gpa > Get GPA"
    await query.message.edit_text(text, reply_markup=main_menu())


@print_msg
async def profile(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user = await aioredis.get_dict(user_id)

    text = ""

    if await aioredis.if_user(user_id):
        text += f"User ID: `{user_id}`\n"
        if await aioredis.is_registered_moodle(user_id):
            text += f"Barcode: `{user['barcode']}`\n"
            text += f"Activated demo: {user['demo']}\n\n"
            if await aioredis.is_active_sub(user_id):
                time = get_diff_time(user['end_date'])
                text += f"Subscription is active for *{time}*"
            else:
                text += "Subscription is *not active*"
        
        await query.message.edit_text(text, reply_markup=main_menu(), parse_mode='MarkdownV2')
        


@print_msg
async def back_main_menu(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    kb = None
    if not await aioredis.if_user(user_id):
        text = "Hi, I'm Pocket Moodle bot!\n" \
                "I was created for receiving notifications about changing grades and deadlines from moodle.astanait.edu.kz\n\n" \
                "All functions and channel are available by subscription. Also I'm giving you 1 month of free use, it will be enough to figure it out"
        kb = start_buttons(kb)
    else:
        if not await aioredis.is_activaited_demo(user_id):
            kb = start_buttons(kb)
        else:
            kb = commands_buttons(kb)
        if not await aioredis.is_registered_moodle(user_id):
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(sub_menu(kb)))

        text = "Choose one and click:"

    await query.message.edit_text(text, reply_markup=kb)
    await state.finish()


async def PrivacyPolicy(message: types.Message, state: FSMContext):
    with open("src/PP.txt") as file:
        text = file.read()
    await message.reply(text, parse_mode='MarkdownV2')


async def UserAgreement(message: types.Message, state: FSMContext):
    with open("src/UA.txt") as file:
        text = file.read()
    await message.reply(text, parse_mode='MarkdownV2')


async def delete_msg(query: types.CallbackQuery):
    try:
        await query.bot.delete_message(query.message.chat.id, query.message.message_id)
        if query.message.reply_to_message:
            await query.bot.delete_message(query.message.chat.id, query.message.reply_to_message.message_id)
        await query.answer()
    except Exception as exc:
        # logger.error(exc)
        await query.answer("Error")


def register_handlers_default(dp: Dispatcher):
    dp.register_message_handler(start, commands="start", state="*")
    dp.register_message_handler(help, commands="help", state="*")
    dp.register_message_handler(msg_to_admin, commands="msg_to_admin", state="*")

    dp.register_message_handler(PrivacyPolicy, commands="PrivacyPolicy", state="*")
    dp.register_message_handler(UserAgreement, commands="UserAgreement", state="*")

    dp.register_callback_query_handler(
        back_main_menu,
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
