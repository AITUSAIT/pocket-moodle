from aiohttp import ClientSession
from typing import TypedDict
from config import OXA_MERCHANT_KEY


response_results = {
    '100': 'Successful operation',
    '102': 'Validating problem - refer to the validation section',
    '103': 'Invalid merchant',
    '104': 'Inactive merchant',
    '105': '',
    '106': '',
    '107': '',
    '108': '',
    '201': '',
    '202': '',
    '203': '',
}

payment_results = {
    '-2': '',
    '-1': '',
    '1': '',
    '2': '',
    '3': '',
}


class Transaction(TypedDict):
    result: int
    message: str
    trackId: int
    payLink: str


class OxaPay:
    session = ClientSession("https://api.oxapay.com")

    async def create_payment(amount:float, desc:str) -> Transaction:
        params = {
            'merchant': OXA_MERCHANT_KEY,
            'amount': amount,
            'description': desc,
            'callbackUrl': "http://93.170.72.95:8080/OxaPay_callback",
        }
        response = await OxaPay.session.post(url='/merchants/request', json=params)

        return await response.json()
    