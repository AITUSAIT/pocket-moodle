import asyncio
import os

import dotenv
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

dotenv.load_dotenv()


bot = Bot(token=os.getenv('TOKEN'))
bot_notify = Bot(token=os.getenv('TOKEN_notify'))
dp = Dispatcher(bot, storage=MemoryStorage())

rate = 1

bot_task: asyncio.Task = None

robo_test = os.getenv('test')
robo_login = os.getenv('ROBO_LOGIN')
robo_passwd_1 = os.getenv('ROBO_PASSWD_1')
robo_passwd_2 = os.getenv('ROBO_PASSWD_2')

tokens = {
    '897sdfkjh34598sdf': 'home server',
    'kj354hs09fug8k': 'pocket moodle server',
    'asdjkhfruiowhtslkj': 'worker server 1',
}

time_periods = [1, 5, 15]

prices = {
    '1': 400,
    '3': 1320,
    '6': 2280,
    '9': 2880,
}

status_codes = {
    0: "Запрос обработан успешно",
    1: "Неверная цифровая подпись запроса",
    2: "Информация о магазине с таким MerchantLogin не найдена или магазин не активирован",
    3: "Информация об операции с таким InvoiceID не найдена",
    4: "Найдено две операции с таким InvoiceID",
    1000: "Внутренняя ошибка сервиса"
}

payment_status_codes = {
    5: "Операция инициализирована, деньги от покупателя не получены",
    10: "Операция отменена, деньги от покупателя не были получены",
    50: "Деньги от покупателя получены, производится зачисление денег на счет магазина",
    60: "Деньги после получения были возвращены покупателю",
    80: "Исполнение операции приостановлено. Внештатная остановка",
    100: "Платёж проведён успешно"
}
