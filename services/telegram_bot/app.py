import json
import os
import threading

from common_utils import configure_logging, decrypt_env_var, get_rabbitmq_connection
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

QUEUE_INPUT = "article.processed"
QUEUE_APPROVED = "article.approved"
QUEUE_REJECTED = "article.rejected"

ADMIN_IDS: set[int] = set()



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    user = update.effective_user
    if user is None or user.id not in ADMIN_IDS:
        await query.answer()
        return

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or user.id not in ADMIN_IDS:
        return




def main() -> None:
    logger = configure_logging()
    logger.info("Telegram bot service starting")

    token = decrypt_env_var("TELEGRAM_BOT_TOKEN")
    admin_ids_raw = os.getenv("TELEGRAM_ADMIN_IDS", "")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    webhook_secret = decrypt_env_var("TELEGRAM_WEBHOOK_SECRET")
    if not token or not admin_ids_raw or not webhook_url or not webhook_secret:
        logger.error(
            "TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS, TELEGRAM_WEBHOOK_URL, or TELEGRAM_WEBHOOK_SECRET not set",
        )
        return

    global ADMIN_IDS
    ADMIN_IDS = {int(x) for x in admin_ids_raw.split(",") if x.strip()}


    application = Application.builder().token(token).build()
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    def run_webhook() -> None:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", "8080")),
            webhook_url=webhook_url,
            secret_token=webhook_secret,
        )

    thread = threading.Thread(target=run_webhook, daemon=True)
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
        for admin_id in ADMIN_IDS:
            bot.send_message(chat_id=admin_id, text=summary, reply_markup=keyboard)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_INPUT, on_message_callback=callback)

    try:
        channel.start_consuming()
    finally:
        channel.close()
        conn.close()


if __name__ == "__main__":
    main()
