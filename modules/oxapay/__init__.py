import json
from typing import TypedDict

from aiohttp import ClientSession

from config import OXA_MERCHANT_KEY, bot_notify, bot
from modules.bot.functions.functions import generate_promocode
from modules.logger import logger

from ..bot.functions.rights import admin_list
from .. import database


response_results = {
    '100': 'Successful operation',
    '102': 'Validating problem - refer to the validation section',
    '103': 'Invalid merchant',
    '104': 'Inactive merchant',
    '105': '',
    '106': '',
    '107': '',
    '108': '',
    '201': 'Already approved',
    '202': 'The order has not been paid or has failed. Read the status table for more information.',
    '203': 'Invalid trackId',
}

payment_results = {
    '-3': 'Canceled by the user',
    '-2': 'Unsuccessful payment',
    '-1': 'Payment pending',
    '1': 'Paid, verified',
    '2': 'Paid, Not verified',
}


class Transaction(TypedDict):
    result: int
    message: str
    trackId: int
    payLink: str

    is_for_promocode: bool
    user_id: int
    months: int
    cost: float
    message_id: int


class OxaPay:
    async def get_coins_list():
        session = ClientSession("https://api.oxapay.com")
        params = {
            'merchant': OXA_MERCHANT_KEY,
        }
        response = await session.post(url='/merchants/allowedCoins', json=params)
        res = response.json()
        return res.get('allowed', [])

    async def create_payment(amount:float, desc:str, email:str) -> Transaction:
        session = ClientSession("https://api.oxapay.com")
        params = {
            'merchant': OXA_MERCHANT_KEY,
            'amount': amount,
            'description': desc,
            'email': email,
            'callbackUrl': "http://93.170.72.95:8080/api/payment",
        }
        response = await session.post(url='/merchants/request', json=params)
        return Transaction(await response.json())

    async def verify_payment(track_id: int, success: bool, status: int, order_id: str):
        session = ClientSession("https://api.oxapay.com")
        if success and status == 2:
            params = {
                'merchant': OXA_MERCHANT_KEY,
                'trackId': track_id
            }
            response = await session.post(url='/merchants/verify', json=params)
            res = response.json()
            transaction: Transaction = database.get_payment(track_id)
            user_id = transaction['user_id']
            months = transaction['months']
            cost = transaction['cost']

            if res['result'] != 100:
                logger.error(f"{user_id} - Payment error - {res} - {transaction}")
                return
            logger.info(f"{user_id} - Verify payment - {res} - {transaction}")
            
            if not transaction['is_for_promocode']:
                await database.activate_subs(user_id, (int(months)*30))
                text = f"You have been added *{int(months)*30} days* of subscription\!"
            else:
                code = await generate_promocode()
                promocode = {
                    'code': code,
                    'days': int(months)*30,
                    'count_of_usage': 1,
                    'usage_settings': 'all',
                    'users': []
                }
                await database.redis1.hset('promocodes', code, json.dumps(promocode))
                text = f"Promo code for *{int(months)*30} days*:\n*`{code}`*"

            text_admin = f"*Новая оплата\! {'Promocode' if transaction['is_for_promocode'] else ''}*\n\n" \
                        f"*Invoice ID*: `{id}`\n" \
                        f"*User ID*: `{user_id}`\n" \
                        f"*Кол\-во месяцев*: {months}\n" \
                        f"*Сумма*: {cost}тг\n"
            
            kb = None
            await bot.edit_message_text(text, user_id, transaction['message_id'], reply_markup=kb, parse_mode="MarkdownV2")
            await bot_notify.send_message(admin_list[0], text_admin, parse_mode='MarkdownV2')