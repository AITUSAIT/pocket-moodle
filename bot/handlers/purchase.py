from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.keyboards.purchase import payment_btn, periods_btns

from bot.objects.logger import print_msg
from bot.keyboards.default import main_menu
from bot.keyboards.moodle import register_moodle_query
from bot.objects import aioredis
from robokassa import generate_payment_link
from config import robo_login, robo_passwd_1, robo_passwd_2


@print_msg
async def demo_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
        await aioredis.activate_demo(user_id)
        if await aioredis.is_registered_moodle(user_id):
            text = "You have activated 1 month subscription!"
            kb = main_menu()
        else:
            text = "You have activated 1 month subscription!\n\n" \
                "Now you need register your Moodle account"
            kb = main_menu(register_moodle_query())
                        
    else:
        if await aioredis.is_activaited_demo(user_id):
            text = "You already have activaited demo"
            kb = main_menu()
        else:
            await aioredis.activate_demo(user_id)
            if await aioredis.is_registered_moodle(user_id):
                text = "You have activated 1 month subscription!"
                kb = main_menu()
            else:
                text = "You have activated 1 month subscription!\n\n" \
                    "Now you need register your Moodle account"
                kb = main_menu(register_moodle_query())

    await query.message.edit_text(text, reply_markup=kb)


@print_msg
async def demo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
        await aioredis.activate_demo(user_id)
        if await aioredis.is_registered_moodle(user_id):
            text = "You have activated 1 month subscription!"
            kb = main_menu()
        else:
            text = "You have activated 1 month subscription!\n\n" \
                "Now you need register your Moodle account"
            kb = main_menu(register_moodle_query())

    else:
        if await aioredis.is_activaited_demo(user_id):
            text = "You already have activaited demo"
            kb = main_menu()
        else:
            await aioredis.activate_demo(user_id)
            if await aioredis.is_registered_moodle(user_id):
                text = "You have activated 1 month subscription!"
                kb = main_menu()
            else:
                text = "You have activated 1 month subscription!\n\n" \
                    "Now you need register your Moodle account"
                kb = main_menu(register_moodle_query())
                
    await message.answer(text, reply_markup=kb)


@print_msg
async def purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns()
    await message.answer(text, reply_markup=kb)


async def purchase_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns()
    await query.message.edit_text(text, reply_markup=kb)


async def create_payment(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    months = int(query.data.split('|')[1])
    if months == 1:
        cost = 480.0
    else:
        return
    link = generate_payment_link(
        merchant_login=robo_login,
        merchant_password_1=robo_passwd_1,
        cost=cost,
        number=query.from_user.id,
        is_test=1,
        description=f"{query.from_user.id}"
    )
    text = "Payment link is ready!"
    kb = payment_btn(link)
    await query.message.edit_text(text, reply_markup=kb)


def register_handlers_purchase(dp: Dispatcher):
    dp.register_message_handler(demo, commands="demo", state="*")
    dp.register_message_handler(purchase, commands="purchase", state="*")

    dp.register_callback_query_handler(
        demo_query,
        lambda c: c.data == "demo",
        state="*"
    )
    dp.register_callback_query_handler(
        purchase_query,
        lambda c: c.data == "purchase",
        state="*"
    )
    dp.register_callback_query_handler(
        create_payment,
        lambda c: c.data.split('|')[0] == "purchase",
        state="*"
    )
