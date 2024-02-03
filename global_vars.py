import asyncio

from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

from config import TOKEN, TOKEN_NOTIFY
from modules.database.models import Server, User

bot_task: asyncio.Task = None
bot = Bot(token=TOKEN)
bot_notify = Bot(token=TOKEN_NOTIFY)
dp = Dispatcher(bot, storage=MemoryStorage())


USERS: list[User] = []
START_TIME = None
SERVERS: list[Server] = []
