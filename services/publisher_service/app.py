import os
from telegram import Bot
from common_utils import configure_logging, get_rabbitmq_connection, session_scope
from services.core_engine.models import Article

QUEUE_APPROVED = "article.approved"


def publish_article(article_id: int, bot: Bot, chat_id: str, logger) -> None:
    """Fetch article from DB and send its text or link to Telegram."""
    with session_scope() as db:
        article = db.get(Article, article_id)
        if not article:
            logger.warning("Article not found", extra={"id": article_id})
            return
        text = (
            article.translated_content
            or article.content
            or article.source_url
            or ""
        )
        if len(text) > 4000:
            text = article.source_url
        bot.send_message(chat_id=chat_id, text=text)
    logger.info("Published article", extra={"id": article_id})


def main() -> None:
    logger = configure_logging()
    logger.info("Publisher service starting")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_PUBLISH_CHAT_ID")
    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_PUBLISH_CHAT_ID not set")
        return

    bot = Bot(token=token)

    conn = get_rabbitmq_connection()
    channel = conn.channel()
    channel.queue_declare(queue=QUEUE_APPROVED, durable=True)

    def callback(ch, method, properties, body):
        try:
            article_id = int(body.decode())
        except ValueError:
            logger.warning("Invalid message body", extra={"body": body})
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        publish_article(article_id, bot, chat_id, logger)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_APPROVED, on_message_callback=callback)

    try:
        channel.start_consuming()
    finally:
        channel.close()
        conn.close()


if __name__ == "__main__":
    main()