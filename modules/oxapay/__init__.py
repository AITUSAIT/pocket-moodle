from aiohttp import ClientSession

from config import OXA_MERCHANT_KEY, TEST, bot, bot_notify, server_port

from ..bot.functions.functions import clear_MD
from ..database import PaymentDB, PromocodeDB, UserDB
from ..database.models import Transaction
from ..logger import Logger

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


class OxaPay:
    async def get_coins_list():
        async with ClientSession("https://api.oxapay.com") as session:
            params = {
                'merchant': OXA_MERCHANT_KEY,
            }
            response = await session.post(url='/merchants/allowedCoins', json=params)
            res = response.json()
            await session.close()
            return res.get('allowed', [])

    async def create_payment(user_id:int, message_id:int, amount:float, months:int, desc:str, email:str, is_for_promocode: bool, ) -> Transaction:
        async with ClientSession("https://api.oxapay.com") as session:
            params = {
                'merchant': OXA_MERCHANT_KEY,
                'amount': amount,
                'description': desc,
                'email': email,
                'callbackUrl': f"http://93.170.72.95:{server_port}/api/payment",
            }
            response = await session.post(url='/merchants/request', json=params)
            data = await response.json()
            data.update({
                'trackId': int(data['trackId']),
                'cost': amount,
                'is_for_promocode': is_for_promocode,
                'months': months,
                'user_id': user_id,
                'user_mail': email,
                'message_id': message_id
            })
            return Transaction(data)

    async def verify_payment(track_id: str, success: str, status: str, order_id: str):
        async with ClientSession("https://api.oxapay.com") as session:
            if success == '1' and status == '2':
                params = {
                    'merchant': OXA_MERCHANT_KEY,
                    'trackId': track_id
                }
                response = await session.post(url='/merchants/inquiry', json=params)
                res = await response.json()
                transaction: Transaction = await PaymentDB.get_payment_by_track_id(int(track_id))
                user_id = transaction['user_id']
                user_mail = transaction['user_mail']
                months = transaction['months']
                cost = transaction['cost']

                if res['result'] != 100:
                    Logger.error(f"Payment error - {res} - {transaction}")
                    return
                Logger.info(f"Verify payment - {res} - {transaction}")
                
                
                if not transaction['is_for_promocode']:
                    if not TEST:
                        await UserDB.activate_sub(user_mail, int(months)*30)
                    text = f"You have been added *{int(months)*30} days* of subscription\!"
                else:
                    code = await PromocodeDB.generate_promocode()
                    promocode = {
                        'code': code,
                        'days': int(months)*30,
                        'count_of_usage': 1,
                        'usage_settings': 'all',
                        'users': []
                    }
                    if not TEST:
                        await PromocodeDB.add_promocode(promocode)
                    text = f"Promo code for *{int(months)*30} days*:\n*`{clear_MD(code)}`*"

                text_admin = f"*Новая оплата\! {'Promocode' if transaction['is_for_promocode'] else ''}*\n\n" \
                            f"*Invoice ID*: `{track_id}`\n" \
                            f"*User ID*: `{user_id}`\n" \
                            f"*User mail*: `{user_mail}`\n" \
                            f"*Кол\-во месяцев*: {clear_MD(months)}\n" \
                            f"*Сумма*: {clear_MD(cost)}$\n"
                
                kb = None
                try:
                    await bot.edit_message_text(text, user_id, transaction['message_id'], reply_markup=kb, parse_mode="MarkdownV2")
                except:
                    await bot.send_message(text, user_id, reply_markup=kb, parse_mode="MarkdownV2")
                await bot_notify.send_message(626591599, text_admin, parse_mode='MarkdownV2')