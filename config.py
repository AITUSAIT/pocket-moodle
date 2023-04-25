import asyncio
import os

import dotenv
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

dotenv.load_dotenv()

server_port = os.getenv('SERVER_PORT', 8080)

bot = Bot(token=os.getenv('TOKEN'))
bot_notify = Bot(token=os.getenv('TOKEN_notify'))
dp = Dispatcher(bot, storage=MemoryStorage())

rate = 1

bot_task: asyncio.Task = None

OXA_MERCHANT_KEY = os.getenv('OXA_MERCHANT_KEY')

robo_test = os.getenv('test')
ROBO_LOGIN = os.getenv('ROBO_LOGIN')
ROBO_PASSWD_1 = os.getenv('ROBO_PASSWD_1')
ROBO_PASSWD_2 = os.getenv('ROBO_PASSWD_2')

tokens = {
    '897sdfkjh34598sdf': 'home server',
    'kj354hs09fug8k': 'pocket moodle server',
    'asdjkhfruiowhtslkj': 'worker server 1',
}

prices = {
    '1': 0.75,
    '3': 2.1,
    '6': 3.9,
    '9': 5.4,
    '12': 6.6,
}
