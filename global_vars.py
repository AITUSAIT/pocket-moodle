from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, TOKEN_NOTIFY

bot = Bot(token=TOKEN)
bot_notify = Bot(token=TOKEN_NOTIFY)
dp = Dispatcher(storage=MemoryStorage())
