from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import dp, prices, rate

from ...database import PaymentDB, UserDB, PromocodeDB
from ...database.models import User
from ...logger import Logger
from ..handlers.moodle import trottle
from ..keyboards.purchase import payment_btn, periods_btns, purchase_btns


class Promo(StatesGroup):
    wait_promocode = State()


@dp.throttled(rate=rate)
@Logger.log_msg
async def purchase(query: types.CallbackQuery, state: FSMContext):
    if query.__class__ is types.CallbackQuery:
        await query.answer()

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
    user = await UserDB.get_user(user_id)
    is_for_promocode = query.data.split()[0] == "purchase_promo"

    if not user:
        await UserDB.create_user(user_id, None)

    text = "Select the payment period:"
    kb = periods_btns(is_for_promocode)
    await query.message.edit_text(text, reply_markup=kb)


@dp.throttled(rate=rate)
async def create_payment(query: types.CallbackQuery, state: FSMContext):
    from ...oxapay import OxaPay, Transaction
    await query.answer()

    user_id = query.from_user.id
    user: User = await UserDB.get_user(user_id)
    is_for_promocode = query.data.split('|')[0] == "purchase_promo"

    months = int(query.data.split('|')[1])
    cost = prices.get(str(months), None)

    if cost is None:
        await query.answer('This plan is not available, please try again')
        return

    desc = f"Pocket Moodle BOT sub for {months} {'months' if months > 1 else 'month'}"
    transaction: Transaction = await OxaPay.create_payment(
        amount=cost,
        desc=desc,
        user_id=user_id,
        email=user.mail,
        months=months,
        message_id=query.message.message_id,
        is_for_promocode=is_for_promocode
    )
    Logger.info(f"{user_id} - Created payment - {transaction}")
    await PaymentDB.create_payment(transaction)

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
    user: User = await UserDB.get_user(user_id)
    promocode = message.text
    
    promocode_info = await PromocodeDB.get_promocode(promocode)
    if not promocode_info:
        await message.reply("❌Wrong Promocode❌")
        return
    
    days = promocode_info['days']
    count_of_usage = promocode_info['count_of_usage']
    usage_settings = promocode_info['usage_settings']
    users = promocode_info['users']

    if user_id in users:
        await message.reply("This promo code has already been activated")
        return

    if usage_settings == "newbie":
        if not user.is_newbie():
            await message.reply("This promo code is only for new users")
            return

    if count_of_usage == 0:
        await message.reply("This promo code is disabled")
        return
    
    await UserDB.activate_sub(user_id, days)
    await PromocodeDB.add_user_to_promocode(promocode_info['code'], user_id)

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
