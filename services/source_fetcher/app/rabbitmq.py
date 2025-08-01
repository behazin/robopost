import aio_pika
import logging

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        logger.info("Connecting to RabbitMQ...")
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        logger.info("Successfully connected to RabbitMQ.")

    async def declare_exchange(self, name: str, type: str = 'topic', durable: bool = True):
        await self.channel.declare_exchange(name, type, durable=durable)
        logger.info(f"Exchange '{name}' declared.")

    async def publish(self, exchange_name: str, routing_key: str, body: bytes):
        exchange = await self.channel.get_exchange(exchange_name)
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published message to exchange '{exchange_name}' with key '{routing_key}'")

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("RabbitMQ connection closed.")