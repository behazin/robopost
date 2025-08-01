import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .processor import ArticleProcessor
from .rabbitmq import RabbitMQClient
from .db import SessionLocal
from .models import Article

class CoreEngineConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient, processor: ArticleProcessor):
        self.rabbitmq_client = rabbitmq_client
        self.processor = processor

    async def on_message(self, channel, method, properties, body):
        try:
            message = json.loads(body)
            url = message.get("url")
            source_id = message.get("source_id")
            logging.info(f"Received new link to process: {url}")

            async with SessionLocal() as db_session:
                # Idempotency Check
                existing_article = await self.processor.get_article_by_url(db_session, url)
                if existing_article:
                    logging.warning(f"Article with URL {url} already exists. Skipping.")
                    await channel.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # Process the article
                article_id = await self.processor.process_new_article(db_session, source_id, url)
                if article_id:
                    # Publish for approval
                    approval_message = {"article_id": article_id}
                    await self.rabbitmq_client.publish(
                        exchange='ex.articles',
                        routing_key='rk.pending_approval',
                        body=json.dumps(approval_message)
                    )
                    logging.info(f"Article {article_id} sent for approval.")

            await channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logging.error(f"Failed to process message: {body}. Error: {e}", exc_info=True)
            await channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Move to DLX

    async def start_consuming(self):
        await self.rabbitmq_client.start_consuming('q.new_links', self.on_message)