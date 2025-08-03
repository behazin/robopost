import os
import time
from typing import Iterable, Set

import feedparser
import schedule

from common_utils import configure_logging, get_rabbitmq_connection


FEEDS_ENV_VAR = "RSS_FEEDS"
INTERVAL_ENV_VAR = "CRAWL_INTERVAL"


def fetch_and_publish(conn, feeds: Iterable[str], seen: Set[str], logger):
    """Fetch feeds and publish new links to RabbitMQ."""
    channel = conn.channel()
    channel.queue_declare(queue="url.new", durable=True)
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:  # pragma: no cover - feedparser exceptions
            logger.exception("Error parsing feed %s: %s", feed_url, exc)
            continue
        for entry in parsed.entries:
            link = entry.get("link")
            if link and link not in seen:
                seen.add(link)
                channel.basic_publish(exchange="", routing_key="url.new", body=link)
                logger.info("Published new URL", extra={"url": link})
    channel.close()


def main():
    logger = configure_logging()
    logger.info("Source crawler starting")

    feeds_env = os.getenv(FEEDS_ENV_VAR, "").split(",")
    feeds = [f.strip() for f in feeds_env if f.strip()]

    conn = get_rabbitmq_connection()
    seen: Set[str] = set()

    interval = int(os.getenv(INTERVAL_ENV_VAR, "60"))
    schedule.every(interval).seconds.do(fetch_and_publish, conn, feeds, seen, logger)

    fetch_and_publish(conn, feeds, seen, logger)
    while True:  # pragma: no cover - infinite loop
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()