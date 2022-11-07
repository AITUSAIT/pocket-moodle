import json
import logging.config
from functools import wraps

from aiogram import types


with open('logs.log', 'w+') as f:
    ...
with open('debug.log', 'w+') as f:
    ...
with open('logger_config.json', 'r') as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger('custom')


def log_msg(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        arg = args[0]
        if arg.__class__ is types.Message:
            arg : types.Message
            if arg.chat.id == arg.from_user.id:
                logger.info(f"{arg.from_user.id} - {arg.text}")
            else:
                logger.info(
                    f"{arg.from_user.id} / {arg.chat.id} - {arg.text}")
            return func(*args, **kwargs)
        elif arg.__class__ is types.CallbackQuery:
            arg : types.CallbackQuery
            if arg.message.chat.id == arg.from_user.id:
                logger.info(f"{arg.from_user.id} - {arg.data}")
            else:
                logger.info(
                    f"{arg.from_user.id} / {arg.message.chat.id} - {arg.data}")
            return func(*args, **kwargs)
    return wrapper
