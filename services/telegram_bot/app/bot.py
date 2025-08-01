from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from .config import settings
from . import handlers
from .rate_limiter import MessageRateLimiter

def create_bot_app(db_session_factory):
    """Creates and configures the Telegram Bot Application."""
    
    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        # Use a connection pool for handling multiple webhook updates concurrently
        .pool_timeout(360)
        .connect_timeout(360)
        .post_init(post_init)
        .build()
    )
    application.bot_data["db_session_factory"] = db_session_factory
    # Initialize the rate limiter: 18 messages per 60 seconds, as requested.
    application.bot_data["rate_limiter"] = MessageRateLimiter(rate_limit=18, per_seconds=60)

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CallbackQueryHandler(handlers.button_callback_handler))

    return application

async def post_init(application):
    await application.bot.set_my_commands([("start", "شروع به کار و ثبت‌نام در سیستم")])