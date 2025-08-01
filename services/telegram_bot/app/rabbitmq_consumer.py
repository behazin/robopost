import asyncio
import json
import logging
import aio_pika
from .handlers import send_approval_request

logger = logging.getLogger(__name__)

# A simple global to hold the client for handlers
_rabbit_client = None

def get_rabbit_client():
    return _rabbit_client

class RabbitMQConsumer:
    def __init__(self, url: str, bot_app, db_session_factory):
        self.url = url
        self.bot_app = bot_app
        self.db_session_factory = db_session_factory
        self.connection = None
        self.channel = None
        global _rabbit_client
        _rabbit_client = self

    async def connect(self):
        logger.info("Connecting to RabbitMQ for consumption...")
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        logger.info("Successfully connected to RabbitMQ.")

    async def on_message(self, message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            try:
                data = json.loads(message.body.decode())
                article_id = data.get("article_id")
                if article_id:
                    rate_limiter = self.bot_app.bot_data.get("rate_limiter")
                    logger.info(f"Received approval request for article_id: {article_id}")
                    await send_approval_request(self.db_session_factory, self.bot_app.bot, article_id, rate_limiter)
                await message.ack()
            except Exception as e:
                logger.error(f"Failed to process approval message: {message.body.decode()}. Error: {e}", exc_info=True)
                await message.nack(requeue=False) # Move to DLX

    async def run(self):
        await self.connect()
        
        # Declare exchanges and queues
        await self.channel.declare_exchange('ex.articles', 'topic', durable=True)
        await self.channel.declare_exchange('ex.dead_letters', 'fanout', durable=True)
        
        queue = await self.channel.declare_queue(
            'q.for_approval',
            durable=True,
            arguments={'x-dead-letter-exchange': 'ex.dead_letters'}
        )
        await queue.bind('ex.articles', 'rk.for_approval')

        logger.info("Telegram Bot is listening for approval messages.")
        await queue.consume(self.on_message)
        # Keep the consumer running
        await asyncio.Event().wait()

    async def publish(self, exchange_name: str, routing_key: str, body: str):
        if not self.channel:
            await self.connect()
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=body.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=routing_key,
        )