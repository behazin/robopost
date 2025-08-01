import asyncio
import json
import logging
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Source, Article
from .rabbitmq import RabbitMQClient

class Fetcher:
    def __init__(self, db: AsyncSession, rabbitmq: RabbitMQClient):
        self.db = db
        self.rabbitmq = rabbitmq
        self.seen_urls = set()

    async def _is_url_processed(self, url: str) -> bool:
        if url in self.seen_urls:
            return True
        result = await self.db.execute(select(Article).where(Article.original_url == url))
        if result.scalars().first():
            self.seen_urls.add(url)
            return True
        return False

    async def fetch_all_sources(self):
        result = await self.db.execute(select(Source))
        sources = result.scalars().all()
        tasks = [self.process_source(source) for source in sources]
        await asyncio.gather(*tasks)

    async def process_source(self, source: Source):
        logging.info(f"Fetching source: {source.name} ({source.url})")
        try:
            feed = feedparser.parse(source.url)
            for entry in feed.entries:
                link = entry.link
                if not await self._is_url_processed(link):
                    logging.info(f"Found new link: {link}")
                    message = {
                        "url": link,
                        "source_id": source.id
                    }
                    await self.rabbitmq.publish(
                        exchange='ex.articles',
                        routing_key='rk.new_link',
                        body=json.dumps(message)
                    )
                    self.seen_urls.add(link)
        except Exception as e:
            logging.error(f"Failed to process source {source.name}: {e}")

    async def close(self):
        await self.db.close()
        await self.rabbitmq.close()