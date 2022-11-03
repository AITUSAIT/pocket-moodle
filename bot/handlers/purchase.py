import xml.etree.ElementTree as ET

import aiohttp
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.functions.rights import is_Admin
from bot.handlers.moodle import trottle
from bot.keyboards.purchase import payment_btn, periods_btns
from bot.objects import aioredis
from bot.objects.logger import print_msg, logger

from config import (dp, prices, rate, robo_login, robo_passwd_1, robo_passwd_2,
                    robo_test, status_codes, payment_status_codes)
from robokassa import calculate_signature, generate_id, generate_payment_link


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
        is_test=int(robo_test),
        description=f"Покупка подписки на {months} месяц(-ев)"
    )

    signature = calculate_signature(
        robo_login,
        id,
        robo_passwd_2
    )
    text = "Payment link is ready!"
    kb = payment_btn(link, id, signature)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(trottle, rate=5)
async def check_payment(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    f, id, signa = query.data.split()

    link = f"https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt?MerchantLogin={robo_login}&InvoiceID={id}&Signature={signa}"
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            data = await resp.text()
            root = ET.fromstring(data)
            result = root[0]

            status = int(result[0].text)
            if status == 0:
                state = root[1]
                payment_status = int(state[0].text)
                await query.answer(payment_status_codes[payment_status])
                if payment_status == 100:
                    info = root[2]
                    cost = int(info[1].text.replace('.000000', ''))
                    user = await aioredis.get_dict(user_id)
                    payment_state = False
                    for key, value in prices.items():
                        if cost == value:
                            await aioredis.activate_subs(user_id, (int(key)*30))
                            text = f"You have been added {int(key)*30} days of subscription!"
                            payment_state = True
                            break
                    enddate_str = await aioredis.get_key(user_id, 'end_date')
                    if payment_state:
                        logger.info(f"{user_id} {key} {user['end_date']} -> {enddate_str}")
                    else:
                        text = "An error occurred during payment\n\nWrite to @dake_duck to solve this problem"
                        logger.error(f"{user_id} Error {user['end_date']} -> {enddate_str}")
                    kb = None
                    await query.message.edit_text(text, reply_markup=kb)
            else:
                await query.answer(status_codes[status])
                logger.error(f"{user_id} {id} {signa} {status_codes[status]}")


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
    dp.register_callback_query_handler(
        check_payment,
        lambda c: c.data.split()[0] == "check_payment",
        state="*"
    )
