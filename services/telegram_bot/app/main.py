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
    
    # Pass the whole application object to the consumer to give it access to bot_data
    consumer = RabbitMQConsumer(settings.RABBITMQ_URL, bot_app, db_session_factory)

    # --- Webhook Setup ---
    # In production, you must use a reverse proxy (e.g., Nginx) to forward
    # requests from a public HTTPS URL to the port defined here.
    await bot_app.bot.set_webhook(
        url=f"{settings.TELEGRAM_WEBHOOK_URL}/{settings.TELEGRAM_BOT_TOKEN}",
        secret_token=settings.TELEGRAM_SECRET_TOKEN
    )

    # Run the bot and the RabbitMQ consumer concurrently
    await asyncio.gather(
        consumer.run(),
        bot_app.run_webhook(listen="0.0.0.0", port=8000, secret_token=settings.TELEGRAM_SECRET_TOKEN)
    )

if __name__ == "__main__":
    asyncio.run(main())