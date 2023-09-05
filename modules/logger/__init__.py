import json
import logging.config
from functools import wraps
from typing import Mapping

from aiogram import types


class Logger(logging.Logger):
    _config_loaded = False
    _config = {}

    @classmethod
    def load_config(cls):
        if not cls._config_loaded:
            try:
                with open('logger_config.json', 'r') as config_file:
                    cls._config = json.load(config_file)
                    cls._config_loaded = True
            except FileNotFoundError:
                cls._config = {}
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in config file")
            logging.config.dictConfig(cls._config)
            cls.logger = logging.getLogger('custom')

    @classmethod
    def log_msg(cls, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            arg = args[0]
            if arg.__class__ is types.Message:
                arg: types.Message
                if arg.chat.id == arg.from_user.id:
                    cls.info(f"{arg.from_user.id} - {arg.text}")
                else:
                    cls.info(
                        f"{arg.from_user.id} / {arg.chat.id} - {arg.text}")

                return func(*args, **kwargs)
            elif arg.__class__ is types.CallbackQuery:
                arg: types.CallbackQuery
                if arg.message.chat.id == arg.from_user.id:
                    cls.info(f"{arg.from_user.id} - {arg.data}")
                else:
                    cls.info(
                        f"{arg.from_user.id} / {arg.message.chat.id} - {arg.data}")

                return func(*args, **kwargs)
        return wrapper

    @classmethod
    def error(cls, msg: object,
              exc_info = None,
              stack_info: bool = False,
              stacklevel: int = 1,
              extra: Mapping[str, object] | None = None):
        cls.logger.error(msg=msg,
                         exc_info=exc_info,
                         stack_info=stack_info,
                         stacklevel=stacklevel,
                         extra=extra)
        
    @classmethod
    def info(cls, msg: object,
              exc_info = None,
              stack_info: bool = False,
              stacklevel: int = 1,
              extra: Mapping[str, object] | None = None):
        cls.logger.info(msg=msg,
                         exc_info=exc_info,
                         stack_info=stack_info,
                         stacklevel=stacklevel,
                         extra=extra)
