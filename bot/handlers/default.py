import random
from datetime import datetime

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.functions.functions import clear_MD, get_diff_time
from bot.functions.rights import admin_list
from bot.keyboards.purchase import purchase_btn
from bot.objects.logger import print_msg
from bot.keyboards.default import commands_buttons, main_menu, profile_btn, sub_menu
from bot.keyboards.moodle import (add_grades_deadlines_btns,
                                  register_moodle_query)
from bot.objects import aioredis
from bot.objects.chats import chat_store
from config import dp, rate


@dp.throttled(rate=rate)
@print_msg
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    days=2

    if len(message.get_args()):
        args = message.get_args()
        if args == 'me':
            user = await aioredis.get_dict(user_id)

            text = ""

            if await aioredis.if_user(user_id):
                text += f"User ID: `{user_id}`\n"
                if await aioredis.is_registered_moodle(user_id):
                    text += f"Barcode: `{user['barcode']}`\n"
                    if await aioredis.is_active_sub(user_id):
                        time = get_diff_time(user['end_date'])
                        text += f"Subscription is active for *{time}*"
                    else:
                        text += "Subscription is *not active*"
                
                await message.answer(text, reply_markup=main_menu(), parse_mode='MarkdownV2')
                return
        else:
            if not await aioredis.if_user(user_id):
                if await aioredis.if_user(args):
                    if await aioredis.is_registered_moodle(args):
                        await aioredis.activate_subs(args, days)
                        text_2 = f"You have been added {days} days of subscription!"
                        await message.bot.send_message(args, text_2, reply_markup=main_menu())
                        days = 7


    kb = None
    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
        await aioredis.activate_subs(user_id, days)
        text = "Hi\! I am Bot for quick and easy work with a Moodle site\.\n\n" \
                "With an active subscription, you will receive:\n" \
                "1\. Notifications about changes in *Grades*\n" \
                "2\. *Deadlines* notification\n" \
                "3\. Notification of a *deadline* that is about to expire\n" \
                "4\. Show *GPA*\n" \
                "5\. Statistics of *attendance* \(general and for each subject\)"
        await message.answer(text, parse_mode='MarkdownV2')
        text = "Steps:\n" \
                "1\. *Register* your Moodle account\n" \
                "2\. *Wait* from 10 minutes to 1 hour, the system needs time to get the data\n" \
                "3\. *Enjoy* and have time to close deadlines\n\n" \
                f"I\'m giving you a *{days}\-days trial period*, then you\'ll have to pay for a subscription\n\n" \
                "By continuing to use the bot, you agree to the *[Privacy Policy](http://pocketmoodle\.ddns\.net/privacy_policy)*, *[User Agreement](http://pocketmoodle\.ddns\.net/user_agreement)*, and *[Contract Offer](http://pocketmoodle\.ddns\.net/oferta)*\n" \
                "Information about the company \-\> /info"
        kb = register_moodle_query(kb)
    else:
        kb = commands_buttons(kb)
        if not await aioredis.is_registered_moodle(user_id):
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(sub_menu(kb)))
        
        text = "Choose one and click:"

    await message.answer(text, reply_markup=kb, parse_mode='MarkdownV2')
    await state.finish()


@dp.throttled(rate=rate)
@print_msg
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


@dp.throttled(rate=rate)
@print_msg
async def commands(query: types.CallbackQuery, state: FSMContext):
    text = "Commands:\n\n" \
            "/start > Start | Info\n" \
            "/help > Help\n" \
            "/msg_to_admin > Write to Admin\n\n" \
            "/purchase > Purchase subscription\n" \
            "/register_moodle > Register or Re-register Moodle account\n" \
            "/get_grades > Get grades\n" \
            "/get_deadlines > Get deadlines\n" \
            "/get_gpa > Get GPA\n" \
            "/get_attendance > Get attendance\n\n" \
            "/photos_to_pdf > Convert photos to PDF"
    await query.message.edit_text(text, reply_markup=main_menu())


@dp.throttled(rate=rate)
@print_msg
async def profile(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user = await aioredis.get_dict(user_id)

    text = ""

    if await aioredis.if_user(user_id):
        text += f"User ID: `{user_id}`\n"
        if await aioredis.is_registered_moodle(user_id):
            text += f"Barcode: `{user['barcode']}`\n"
            if await aioredis.is_active_sub(user_id):
                time = get_diff_time(user['end_date'])
                text += f"Subscription is active for *{time}*"
            else:
                text += "Subscription is *not active*"
            text += f"\n\n[Promo\-link]({clear_MD(f'https://t.me/pocket_moodle_aitu_bot?start={user_id}')}) \- share it to get 2days sub for every new user"
        
        await query.message.edit_text(text, reply_markup=purchase_btn(), parse_mode='MarkdownV2', disable_web_page_preview=True)
        

@dp.throttled(rate=rate)
@print_msg
async def back_main_menu(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    kb = None
    if not await aioredis.if_user(user_id):
        text = "Hi\! I am Bot for quick and easy work with a Moodle site\.\n\n" \
                "1\. *Register* your Moodle account\n" \
                "2\. *Wait* from 10 minutes to 1 hour, the system needs time to get the data\n" \
                "3\. *Enjoy* and have time to close deadlines"
        kb = register_moodle_query(commands_buttons(kb))
    else:
        kb = commands_buttons(kb)
        if not await aioredis.is_registered_moodle(user_id):
            kb = register_moodle_query(kb)
        else:
            kb = add_grades_deadlines_btns(profile_btn(sub_menu(kb)))

        text = "Choose one and click:"

    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')
    await state.finish()


@dp.throttled(rate=rate)
async def info(message: types.Message, state: FSMContext):
    text = "РЕКВИЗИТЫ ИП\n\n" \
            "ИП «Pocket Moodle»\n" \
            "Юридический адрес: Республика Казахстан,060011, Акмолинская область, г. Астана, ул. Сарыарка 11\n" \
            "РНН: 391720292111\n" \
            "ИИК: в АО «Народный Банк Казахстана»\n" \
            "БИК: HSBKKZKX\n" \
            "Кбе: 19\n\n" \
            "Проверить: kgd.gov.kz/ru/services/taxpayer_search"
    await message.reply(text)


@dp.throttled(rate=rate)
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

    dp.register_message_handler(info, commands="info", state="*")


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
