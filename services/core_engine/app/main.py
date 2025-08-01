import asyncio
import json
import logging
import logging.config
from functools import partial

from .config import settings
from .database import get_session
from .rabbitmq import RabbitMQClient
from .processor import ArticleProcessor
from .monitoring import setup_monitoring_app

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

async def on_message(
    message: "AbstractIncomingMessage",
    processor: ArticleProcessor,
    rabbit_client: RabbitMQClient
):
    """Callback function to process a message from RabbitMQ."""
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode()
            logger.info(f"Received message: {body}")
            data = json.loads(body)
            
            article_id = await processor.process_article(data['url'], data['source_id'])

            if article_id:
                # Publish to the next queue for admin approval
                approval_message = {"article_id": article_id}
                await rabbit_client.publish(
                    exchange_name='ex.articles',
                    routing_key='rk.for_approval',
                    body=json.dumps(approval_message)
                )
                logger.info(f"Article {article_id} processed and sent for approval.")
            
            await message.ack()
        except Exception:
            logger.error(f"Failed to process message: {message.body.decode()}", exc_info=True)
            await message.nack(requeue=False) # Move to DLX

async def main():
    """Main function to run the Core Engine service."""
    logger.info("Starting Core Engine service...")

    # Start monitoring server
    monitoring_app = setup_monitoring_app()
    asyncio.create_task(monitoring_app.run(host="0.0.0.0", port=settings.METRICS_PORT))

    # Initialize services
    db_session_factory = get_session
    processor = ArticleProcessor(db_session_factory)
    rabbit_client = RabbitMQClient(settings.RABBITMQ_URL)
    
    await rabbit_client.connect()

    # Declare exchanges and queues
    await rabbit_client.declare_exchange('ex.articles', 'topic')
    await rabbit_client.declare_exchange('ex.dead_letters', 'fanout')
    
    await rabbit_client.declare_queue(
        'q.links.to_process',
        durable=True,
        arguments={'x-dead-letter-exchange': 'ex.dead_letters'}
    )
    await rabbit_client.bind_queue('q.links.to_process', 'ex.articles', 'rk.new_link')

    # Start consuming messages
    callback = partial(on_message, processor=processor, rabbit_client=rabbit_client)
    await rabbit_client.consume('q.links.to_process', callback)

    logger.info("Core Engine is listening for messages.")

if __name__ == "__main__":
    asyncio.run(main())