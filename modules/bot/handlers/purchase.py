from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET

import aiohttp
from aiogram import Dispatcher, types
from aiogram.types.message import ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import (bot_notify, dp, payment_status_codes, prices, rate,
                    robo_login, robo_passwd_1, robo_passwd_2, robo_test,
                    status_codes)
from robokassa import calculate_signature, generate_id, generate_payment_link

from ... import database
from ... import logger as Logger
from ...logger import logger
from ..functions.functions import generate_promocode
from ..functions.rights import admin_list
from ..handlers.moodle import trottle
from ..keyboards.purchase import payment_btn, periods_btns, purchase_btns
from ...scheduler import EventsScheduler
from config import bot, time_periods


class Promo(StatesGroup):
    wait_promocode = State()


async def check_payment_scheduled(user_id, id, signa, is_for_promocode, minutes, chat_id, message_id):
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

                if payment_status == 100:
                    info = root[2]
                    cost = int(info[1].text.replace('.000000', ''))
                    user = await database.get_dict(user_id)
                    payment_state = False
                    for key, value in prices.items():
                        if cost == value:
                            if not is_for_promocode:
                                await database.activate_subs(user_id, (int(key)*30))
                            else:
                                code = await generate_promocode()
                                promocode = {
                                    'code': code,
                                    'days': int(key)*30,
                                    'count_of_usage': 1,
                                    'usage_settings': 'all',
                                    'users': []
                                }
                                await database.redis1.hset('promocodes', code, json.dumps(promocode))
                            payment_state = True
                            break
                    enddate_str = await database.get_key(user_id, 'end_date')

                    if payment_state:
                        for min in time_periods:
                            try:
                                EventsScheduler.scheduler.remove_job(f"{user_id}_{id}_{min}", jobstore='sqlite')
                            except:
                                ...
                        if not is_for_promocode:
                            text = f"You have been added *{int(key)*30} days* of subscription\!"
                            logger.info(f"{user_id} {key} {user.get('end_date', None)} -> {enddate_str}")
                        else:
                            text = f"Promo code for *{int(key)*30} days*:\n*`{code}`*"
                            logger.info(f"{user_id} {key} {code}")

                        text_admin = f"*Новая оплата\! {'Promocode' if is_for_promocode else ''}*\n\n" \
                                    f"*Invoice ID*: `{id}`\n" \
                                    f"*User ID*: `{user_id}`\n" \
                                    f"*Кол\-во месяцев*: {key}\n" \
                                    f"*Сумма*: {cost}тг\n"
                    else:
                        text = "An error occurred during payment\n\nWrite to @dake_duck to solve this problem"
                        logger.error(f"{user_id} {id} {user.get('end_date', None)} Error")

                        text_admin = "*Ошибка оплаты\!*\n\n" \
                                    f"*Invoice ID*: `{id}`\n" \
                                    f"*User ID*: `{user_id}`\n" \
                                    f"*Сумма*: {cost}тг\n" \
                                    f"*Signa*: `{signa}`"

                    kb = None
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="MarkdownV2")

                    await bot_notify.send_message(admin_list[0], text_admin, parse_mode='MarkdownV2')
            else:
                print(status_codes[status])
    try:
        EventsScheduler.scheduler.remove_job(f"{user_id}_{id}_{minutes}", jobstore='sqlite')
    except:
        ...
    

@dp.throttled(rate=rate)
@Logger.log_msg
async def purchase(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    if not await database.if_user(user_id):
        await database.new_user(user_id)

    if query.__class__ is types.CallbackQuery:

        text = "Select the payment option:"
        kb = purchase_btns()
        await query.message.edit_text(text, reply_markup=kb)

    elif query.__class__ is types.Message:
        message : types.Message = query

        text = "Select the payment option:"
        kb = purchase_btns()
        await message.answer(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def purchase_sub(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id
    is_for_promocode = query.data.split()[0] == "purchase_promo"

    if not await database.if_user(user_id):
        await database.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns(is_for_promocode)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def create_payment(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    months = int(query.data.split('|')[1])
    cost = prices[f'{months}']

    inv_id = await generate_id(query.from_user.id)

    is_for_promocode = query.data.split('|')[0] == "purchase_promo"

    await bot.send_invoice(
        query.from_user.id,
        title='Payment',
        description='Pocket Moodle subscription',
        provider_token='',
        currency='kzt',
        is_flexible=False,
        prices=[types.LabeledPrice(label=f'Subscription for {months} month', amount=cost*100)],
        payload=f'{months} {is_for_promocode}',
        provider_data= {"InvoiceId": inv_id}
    )


async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def process_successful_payment(message: types.Message):
    print('successful_payment:')
    pmnt = message.successful_payment.to_python()
    for key, val in pmnt.items():
        print(f'{key} = {val}')

    await bot.send_message(
        message.chat.id,
        f"{message.successful_payment.total_amount // 100} {message.successful_payment.currency}"
    )


@dp.throttled(trottle, rate=5)
async def check_payment(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    f, id, signa = query.data.split()
    is_for_promocode = f == "check_payment_promo"

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
                    user = await database.get_dict(user_id)
                    payment_state = False
                    for key, value in prices.items():
                        if cost == value:
                            if not is_for_promocode:
                                await database.activate_subs(user_id, (int(key)*30))
                            else:
                                code = await generate_promocode()
                                promocode = {
                                    'code': code,
                                    'days': int(key)*30,
                                    'count_of_usage': 1,
                                    'usage_settings': 'all',
                                    'users': []
                                }
                                await database.redis1.hset('promocodes', code, json.dumps(promocode))
                            payment_state = True
                            break
                    enddate_str = await database.get_key(user_id, 'end_date')

                    if payment_state:
                        for minutes in time_periods:
                            try:
                                EventsScheduler.scheduler.remove_job(f"{user_id}_{id}_{minutes}", jobstore='sqlite')
                            except:
                                ...
                        if not is_for_promocode:
                            text = f"You have been added *{int(key)*30} days* of subscription\!"
                            logger.info(f"{user_id} {key} {user.get('end_date', None)} -> {enddate_str}")
                        else:
                            text = f"Promo code for *{int(key)*30} days*:\n*`{code}`*"
                            logger.info(f"{user_id} {key} {code}")

                        text_admin = f"*Новая оплата\! {'Promocode' if is_for_promocode else ''}*\n\n" \
                                    f"*Invoice ID*: `{id}`\n" \
                                    f"*User ID*: `{user_id}`\n" \
                                    f"*Кол\-во месяцев*: {key}\n" \
                                    f"*Сумма*: {cost}тг\n"
                    else:
                        text = "An error occurred during payment\n\nWrite to @dake_duck to solve this problem"
                        logger.error(f"{user_id} {id} {user.get('end_date', None)} Error")

                        text_admin = "*Ошибка оплаты\!*\n\n" \
                                    f"*Invoice ID*: `{id}`\n" \
                                    f"*User ID*: `{user_id}`\n" \
                                    f"*Сумма*: {cost}тг\n" \
                                    f"*Signa*: `{signa}`"

                    kb = None
                    await query.message.edit_text(text, reply_markup=kb, parse_mode="MarkdownV2")

                    await bot_notify.send_message(admin_list[0], text_admin, parse_mode='MarkdownV2')
            else:
                await query.answer(status_codes[status])


@dp.throttled(trottle, rate=rate)
async def promocode(message: types.Message, state: FSMContext):    
    await message.reply("Write Promocode:")
    await Promo.wait_promocode.set()


@dp.throttled(trottle, rate=rate)
async def enter_promocode(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    promocode = message.text
    
    if not await database.redis1.hexists('promocodes', promocode):
        await message.reply("❌Wrong Promocode❌")
        return
    
    promocode_info = json.loads(await database.redis1.hget('promocodes', promocode))
    days = promocode_info['days']
    count_of_usage = promocode_info['count_of_usage']
    usage_settings = promocode_info['usage_settings']
    users = promocode_info['users']

    if user_id in users:
        await message.reply("This promo code has already been activated")
        return

    if usage_settings == "newbie":
        if not await database.is_new_user(user_id):
            await message.reply("This promo code is only for new users")
            return

    if count_of_usage == 0:
        await message.reply("This promo code is disabled")
        return
    
    promocode_info['users'].append(user_id)
    promocode_info['count_of_usage'] -= 1
    
    await database.activate_subs(user_id, days)
    await database.redis1.hset('promocodes', promocode, json.dumps(promocode_info))
    text = f"You have been added {days} days of subscription!"
    await message.reply(text)
            

def register_handlers_purchase(dp: Dispatcher):
    dp.register_message_handler(purchase, commands="purchase", state="*")

    dp.register_message_handler(promocode, commands="promocode", state="*")
    dp.register_message_handler(enter_promocode, content_types=['text'], state=Promo.wait_promocode)

    dp.register_pre_checkout_query_handler(process_pre_checkout_query)
    dp.register_message_handler(process_successful_payment, content_types=ContentTypes.SUCCESSFUL_PAYMENT)
    

    dp.register_callback_query_handler(
        purchase,
        lambda c: c.data == "purchase",
        state="*"
    )

    dp.register_callback_query_handler(
        purchase_sub,
        lambda c: c.data == "purchase_sub" or \
            c.data == "purchase_promo",
        state="*"
    )
    dp.register_callback_query_handler(
        create_payment,
        lambda c: c.data.split('|')[0] == "purchase_sub" or \
            c.data.split('|')[0] == "purchase_promo",
        state="*"
    )
    dp.register_callback_query_handler(
        check_payment,
        lambda c: c.data.split()[0] == "check_payment" or \
            c.data.split()[0] == "check_payment_promo",
        state="*"
    )
