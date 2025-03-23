from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, TOKEN_NOTIFY

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
