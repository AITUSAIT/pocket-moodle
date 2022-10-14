import asyncio
import os

import dotenv
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

dotenv.load_dotenv()


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

rate = 1

bot_task: asyncio.Task = None

robo_login = os.getenv('ROBO_LOGIN')
robo_passwd_1 = os.getenv('ROBO_PASSWD_1')
robo_passwd_2 = os.getenv('ROBO_PASSWD_2')

tokens = {
    '897sdfkjh34598sdf': 'home server',
    'kj354hs09fug8k': 'pocket moodle server',
    'asdjkhfruiowhtslkj': 'worker server 1',
}

prices = {
    '1': 480,
    '3': 1320,
    '6': 2280,
    '9': 2880,
}


class Suspendable:
    def __init__(self, target):
        self._target = target
        self._can_run = asyncio.Event()
        self._can_run.set()
        self._task = asyncio.ensure_future(self)

    def __await__(self):
        target_iter = self._target.__await__()
        iter_send, iter_throw = target_iter.send, target_iter.throw
        send, message = iter_send, None
        while True:
            try:
                while not self._can_run.is_set():
                    yield from self._can_run.wait().__await__()
            except BaseException as err:
                send, message = iter_throw, err

            try:
                signal = send(message)
            except StopIteration as err:
                return err.value
            else:
                send = iter_send
            try:
                message = yield signal
            except BaseException as err:
                send, message = iter_throw, err

    def suspend(self):
        self._can_run.clear()

    def is_suspended(self):
        return not self._can_run.is_set()

    def resume(self):
        self._can_run.set()

    def get_task(self):
        return self._task
