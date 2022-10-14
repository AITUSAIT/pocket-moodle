from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.functions.rights import is_Admin
from bot.keyboards.purchase import payment_btn, periods_btns

from bot.objects.logger import print_msg
from bot.objects import aioredis
from robokassa import generate_id, generate_payment_link
from config import robo_login, robo_passwd_1, prices, dp, rate


@dp.throttled(rate=rate)
@print_msg
async def purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns()
    await message.answer(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def purchase_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns()
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
@is_Admin
async def create_payment(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    months = int(query.data.split('|')[1])
    cost = prices[f'{months}']

    id = await generate_id(query.from_user.id)
    link = generate_payment_link(
        merchant_login=robo_login,
        merchant_password_1=robo_passwd_1,
        cost=cost,
        number=id,
        is_test=1,
        description=f"Покупка подписки на {months} месяц(-ев)"
    )
    text = "Payment link is ready!"
    kb = payment_btn(link)
    await query.message.edit_text(text, reply_markup=kb)


def register_handlers_purchase(dp: Dispatcher):
    dp.register_message_handler(purchase, commands="purchase", state="*")

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
