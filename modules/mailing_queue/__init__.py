import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractRobustQueue

from config import RB_HOST, RB_PASS, RB_PORT, RB_USERNAME
from modules.logger import Logger
from modules.mailing_queue.models import MailingModel


class MailingQueue:
    connection: AbstractRobustConnection
    mailingChannel: AbstractRobustChannel
    queue: AbstractRobustQueue

    @classmethod
    async def connect(cls):
        cls.connection = await aio_pika.connect_robust(
            host=RB_HOST,
            port=RB_PORT,
            login=RB_USERNAME,
            password=RB_PASS,
        )
        cls.mailingChannel = await cls.connection.channel()

    @classmethod
    async def push(cls, mailing: MailingModel):
        try:
            await cls.connect()
            body = mailing.model_dump_json().encode()

            async with cls.connection:
                async with cls.mailingChannel:
                    cls.queue = await cls.mailingChannel.declare_queue("mailing_queue", durable=True)
                    message = aio_pika.Message(body=body)
                    await cls.mailingChannel.default_exchange.publish(routing_key=cls.queue.name, message=message)
        except Exception as exc:
            Logger.error(str(exc), exc_info=True)
        finally:
            await cls.close()

    @classmethod
    async def close(cls):
        if not cls.connection.is_closed:
            await cls.connection.close()
