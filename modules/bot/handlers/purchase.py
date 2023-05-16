import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import dp, prices, rate

from ...database import DB
from ... import logger as Logger
from ...logger import logger
from ..handlers.moodle import trottle
from ..keyboards.purchase import payment_btn, periods_btns, purchase_btns


class Promo(StatesGroup):
    wait_promocode = State()


@dp.throttled(rate=rate)
@Logger.log_msg
async def purchase(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    if not await DB.if_user(user_id):
        await DB.new_user(user_id)

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

    if not await DB.if_user(user_id):
        await DB.new_user(user_id)

    text = "Select the payment period:"
    kb = periods_btns(is_for_promocode)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def create_payment(query: types.CallbackQuery, state: FSMContext):
    from ...oxapay import OxaPay, Transaction
    await query.answer()

    user_id = query.from_user.id
    months = int(query.data.split('|')[1])
    cost = prices.get(str(months), None)

    if cost is None:
        await query.answer('This plan is not available, please try again')
        return

    is_for_promocode = query.data.split('|')[0] == "purchase_promo"
    email = await DB.get_email(user_id)
    desc = f"Pocket Moodle BOT sub for {months} {'months' if months > 1 else 'month'}"
    transaction: Transaction = await OxaPay.create_payment(amount=cost, desc=desc, email=email)
    transaction.update({
        'cost': cost,
        'is_for_promocode': is_for_promocode,
        'months': months,
        'user_id': user_id,
        'message_id': query.message.message_id
    })
    logger.info(f"{user_id} - Created payment - {transaction}")
    await DB.save_new_payment(transaction)

    text = "Payment link is ready\!\n\nAfter payment, it will be processed *automatically* \(just need to wait\)"
    kb = payment_btn(transaction['payLink'])
    await query.message.edit_text(text, reply_markup=kb, parse_mode='MarkdownV2')

    
@dp.throttled(trottle, rate=rate)
async def promocode(message: types.Message, state: FSMContext):    
    await message.reply("Write Promocode:")
    await Promo.wait_promocode.set()


@dp.throttled(trottle, rate=rate)
async def enter_promocode(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    promocode = message.text
    
    if not await DB.redis1.hexists('promocodes', promocode):
        await message.reply("❌Wrong Promocode❌")
        return
    
    promocode_info = json.loads(await DB.redis1.hget('promocodes', promocode))
    days = promocode_info['days']
    count_of_usage = promocode_info['count_of_usage']
    usage_settings = promocode_info['usage_settings']
    users = promocode_info['users']

    if user_id in users:
        await message.reply("This promo code has already been activated")
        return

    if usage_settings == "newbie":
        if not await DB.is_new_user(user_id):
            await message.reply("This promo code is only for new users")
            return

    if count_of_usage == 0:
        await message.reply("This promo code is disabled")
        return
    
    promocode_info['users'].append(user_id)
    promocode_info['count_of_usage'] -= 1
    
    await DB.activate_subs(user_id, days)
    await DB.redis1.hset('promocodes', promocode, json.dumps(promocode_info))
    text = f"You have been added {days} days of subscription!"
    await message.reply(text)
            

def register_handlers_purchase(dp: Dispatcher):
    dp.register_message_handler(purchase, commands="purchase", state="*")

    dp.register_message_handler(promocode, commands="promocode", state="*")
    dp.register_message_handler(enter_promocode, content_types=['text'], state=Promo.wait_promocode)
    

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
