from typing import Any, MutableMapping

from aiohttp import ClientSession

import global_vars
from config import OXA_MERCHANT_KEY, SERVER_PORT, TEST
from modules.bot.functions.functions import clear_md
from modules.database import PaymentDB, PromocodeDB, UserDB
from modules.database.models import Transaction
from modules.logger import Logger

response_results = {
    "100": "Successful operation",
    "102": "Validating problem - refer to the validation section",
    "103": "Invalid merchant",
    "104": "Inactive merchant",
    "105": "",
    "106": "",
    "107": "",
    "108": "",
    "201": "Already approved",
    "202": "The order has not been paid or has failed. Read the status table for more information.",
    "203": "Invalid trackId",
}

payment_results = {
    "-3": "Canceled by the user",
    "-2": "Unsuccessful payment",
    "-1": "Payment pending",
    "1": "Paid, verified",
    "2": "Paid, Not verified",
}


class OxaPay:
    @classmethod
    async def get_coins_list(cls):
        async with ClientSession("https://api.oxapay.com") as session:
            params = {
                "merchant": OXA_MERCHANT_KEY,
            }
            response = await session.post(url="/merchants/allowedCoins", json=params)
            res = response.json()
            await session.close()
            return res.get("allowed", [])

    @classmethod
    async def create_payment(
        cls,
        user_id: int,
        message_id: int,
        amount: float,
        months: int,
        desc: str,
        email: str,
        is_for_promocode: bool,
    ) -> Transaction:
        async with ClientSession("https://api.oxapay.com") as session:
            params = {
                "merchant": OXA_MERCHANT_KEY,
                "amount": amount,
                "description": desc,
                "email": email,
                "callbackUrl": f"http://93.170.72.95:{SERVER_PORT}/api/payment",
            }
            response = await session.post(url="/merchants/request", json=params)
            data = await response.json()
            data.update(
                {
                    "trackId": int(data["trackId"]),
                    "cost": amount,
                    "is_for_promocode": is_for_promocode,
                    "months": months,
                    "user_id": user_id,
                    "user_mail": email,
                    "message_id": message_id,
                }
            )
            return Transaction(data)

    @classmethod
    async def verify_payment(cls, data: MutableMapping[str, Any]):
        track_id = int(data["trackId"])
        status = data["status"]
        transaction: Transaction = await PaymentDB.get_payment_by_track_id(int(track_id))
        user_id = transaction["user_id"]

        if status == "Confirming":
            text = "The payment is *confirming*, please wait"
            try:
                await global_vars.bot.edit_message_text(
                    text, user_id, transaction["message_id"], parse_mode="MarkdownV2"
                )
            except Exception:
                pass
        elif status == "Expired":
            await PaymentDB.delete_payment(track_id)
            kb = None
            text = "The payment link has *expired*"
            try:
                await global_vars.bot.edit_message_text(
                    text, user_id, transaction["message_id"], reply_markup=kb, parse_mode="MarkdownV2"
                )
            except Exception:
                pass
        elif status == "Paid":
            await PaymentDB.update_payment(transaction)
            user_id = transaction["user_id"]
            user_mail = transaction["user_mail"]
            months = transaction["months"]
            cost = transaction["cost"]

            Logger.info(f"Verify payment - {data} - {transaction}")

            if not transaction["is_for_promocode"]:
                if not TEST:
                    await UserDB.activate_sub(user_id, int(months) * 30)
                text = f"You have been added *{int(months)*30} days* of subscription\!"
            else:
                code = await PromocodeDB.generate_promocode()
                promocode = {
                    "code": code,
                    "days": int(months) * 30,
                    "count_of_usage": 1,
                    "usage_settings": "all",
                    "users": [],
                }
                if not TEST:
                    await PromocodeDB.add_promocode(promocode)
                text = f"Promo code for *{int(months)*30} days*:\n*`{clear_md(code)}`*"

            text_admin = (
                f"*Новая оплата\! {'Promocode' if transaction['is_for_promocode'] else ''}*\n\n"
                f"*Invoice ID*: `{track_id}`\n"
                f"*User ID*: `{user_id}`\n"
                f"*User mail*: `{user_mail}`\n"
                f"*Кол\-во месяцев*: {clear_md(months)}\n"
                f"*Сумма*: {clear_md(cost)}$\n"
            )

            kb = None
            try:
                await global_vars.bot.edit_message_text(
                    text, user_id, transaction["message_id"], reply_markup=kb, parse_mode="MarkdownV2"
                )
            except Exception:
                await global_vars.bot.send_message(text, user_id, reply_markup=kb, parse_mode="MarkdownV2")
            await global_vars.bot_notify.send_message(626591599, text_admin, parse_mode="MarkdownV2")
