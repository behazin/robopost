import asyncio
import logging
import logging.config

from .config import settings
from .bot import create_bot_app
from .rabbitmq_consumer import RabbitMQConsumer
from .database import get_session_factory, init_db
from .monitoring import setup_monitoring_app

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Telegram Bot service...")
    await init_db()

    # Start monitoring server
    monitoring_app = setup_monitoring_app()
    asyncio.create_task(monitoring_app.run(host="0.0.0.0", port=settings.METRICS_PORT))

    db_session_factory = get_session_factory()
    bot_app = create_bot_app(db_session_factory)
    
    consumer = RabbitMQConsumer(settings.RABBITMQ_URL, bot_app.bot, db_session_factory)

    # Run bot and consumer concurrently
    await asyncio.gather(consumer.run(), bot_app.run_polling())

if __name__ == "__main__":
    asyncio.run(main())