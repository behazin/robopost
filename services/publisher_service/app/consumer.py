import asyncio
import json
import logging
import aio_pika

# Make sure to import the task from where it's defined.
# Assuming it's in tasks.py which is included by celery_app.py
from app.tasks import publish_article_task

from .config import settings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    rabbitmq_url = settings.RABBITMQ_URL 

    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange('ex.articles', aio_pika.ExchangeType.TOPIC, durable=True)
        
        queue = await channel.declare_queue('q.publication.approved', durable=True)
        await queue.bind(exchange, 'rk.publication.approved')

        logging.info("Publisher consumer is waiting for approved articles...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    article_id = data.get('article_id')
                    destination_id = data.get('destination_id')
                    if article_id and destination_id:
                        logging.info(f"Received approval for article {article_id} to destination {destination_id}. Enqueuing Celery task.")
                        # Enqueue the task for the Celery worker
                        publish_article_task.apply_async(kwargs={'article_id': article_id, 'destination_id': destination_id}, queue='q.publication')

if __name__ == "__main__":
    asyncio.run(main())