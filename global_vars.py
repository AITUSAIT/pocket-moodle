from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, TOKEN_NOTIFY
from modules.database.models import Server, User

bot = Bot(token=TOKEN)
bot_notify = Bot(token=TOKEN_NOTIFY)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


USERS: list[User] = []
START_TIME = float("-inf")
SERVERS: dict[str, Server] = {}
