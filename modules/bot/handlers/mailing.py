import pika
from aiogram import Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from config import RATE, RB_PASS, RB_USERNAME
from modules.bot.throttling import rate_limit
from modules.logger import Logger


@rate_limit(limit=RATE)
@Logger.log_msg
async def send_message_to_mailing(message: types.Message, state: FSMContext):
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="0.0.0.0",
            port=5672,
            credentials=pika.PlainCredentials(username=RB_USERNAME, password=RB_PASS),
            heartbeat=30,
            connection_attempts=20,
            retry_delay=0.5,
        )
    )
    try:
        channel = conn.channel()
        channel.queue_declare(queue="hello")
        channel.basic_publish(exchange="", routing_key="hello", body=message.text)
    finally:
        conn.close()


def register_mailing_handlers(dp: Dispatcher):
    dp.message.register(send_message_to_mailing, Command("send_message"))
