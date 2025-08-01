import logging
import asyncio
import telegram
from telegram.constants import ParseMode

from .base import BasePublisher
from ..models import Article

logger = logging.getLogger(__name__)

class TelegramPublisher(BasePublisher):

    @staticmethod
    def publish(credentials: dict, article: Article):
        """
        Publishes an article to a Telegram channel.
        Since Celery tasks are synchronous and python-telegram-bot is async,
        we run the async publishing logic in a dedicated event loop.
        """
        return asyncio.run(TelegramPublisher.async_publish(credentials, article))

    @staticmethod
    async def async_publish(credentials: dict, article: Article):
        bot = telegram.Bot(token=credentials['bot_token'])
        channel_id = credentials['channel_id']
        
        # NOTE: MarkdownV2 is very strict. Ensure any special characters in title/content are escaped.
        # For simplicity, we are using HTML parse mode which is more lenient.
        text = f"<b>{article.processed_title}</b>\n\n{article.processed_content}\n\n<a href='{article.original_url}'>لینک اصلی</a>"
        
        await bot.send_message(chat_id=channel_id, text=text, parse_mode=ParseMode.HTML)
        logger.info(f"Article {article.id} published to Telegram channel {channel_id}")