import json
import os
import threading

from common_utils import configure_logging, get_rabbitmq_connection
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

QUEUE_INPUT = "article.processed"
QUEUE_APPROVED = "article.approved"
QUEUE_REJECTED = "article.rejected"


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    action, article_id = data.split(":", 1)
    queue_name = QUEUE_APPROVED if action == "approve" else QUEUE_REJECTED
    conn = get_rabbitmq_connection()
    channel = conn.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(exchange="", routing_key=queue_name, body=article_id.encode())
    channel.close()
    conn.close()
    await query.edit_message_reply_markup(reply_markup=None)


def main() -> None:
    logger = configure_logging()
    logger.info("Telegram bot service starting")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID not set")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CallbackQueryHandler(handle_callback))
    thread = threading.Thread(target=application.run_polling, daemon=True)
    thread.start()

    bot = Bot(token=token)

    conn = get_rabbitmq_connection()
    channel = conn.channel()
    channel.queue_declare(queue=QUEUE_INPUT, durable=True)

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON", extra={"body": body})
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        article_id = str(message.get("id", ""))
        summary = message.get("summary", "")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Approve", callback_data=f"approve:{article_id}"),
                    InlineKeyboardButton("Reject", callback_data=f"reject:{article_id}"),
                ]
            ]
        )
        bot.send_message(chat_id=chat_id, text=summary, reply_markup=keyboard)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_INPUT, on_message_callback=callback)

    try:
        channel.start_consuming()
    finally:
        channel.close()
        conn.close()


if __name__ == "__main__":
    main()
