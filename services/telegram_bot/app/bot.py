from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from .config import settings
from . import handlers

def create_bot_app(db_session_factory):
    """Creates and configures the Telegram Bot Application."""
    
    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    application.bot_data["db_session_factory"] = db_session_factory

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CallbackQueryHandler(handlers.button_callback_handler))

    return application

async def post_init(application):
    await application.bot.set_my_commands([("start", "شروع به کار و ثبت‌نام در سیستم")])