import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import Admin, Article, Destination, AdminDestinationMap
from .rabbitmq_consumer import get_rabbit_client

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with context.bot_data["db_session_factory"]() as session:
        # Register or update admin info
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == str(user.id)))
        if not admin:
            admin = Admin(telegram_id=str(user.id), name=user.full_name)
            session.add(admin)
            await session.commit()
            await update.message.reply_text(f"سلام {user.full_name}! شما با موفقیت در سیستم ثبت شدید.")
        else:
            await update.message.reply_text(f"خوش آمدید {user.full_name}!")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    action, article_id_str, dest_id_str = query.data.split(':')
    article_id = int(article_id_str)
    destination_id = int(dest_id_str)

    async with context.bot_data["db_session_factory"]() as session:
        # Security check: Does this admin manage this destination?
        admin_q = select(Admin).where(Admin.telegram_id == str(user.id))
        admin = await session.scalar(admin_q)
        if not admin:
            await query.answer("شما به عنوان ادمین ثبت نشده‌اید.", show_alert=True)
            return

        q = select(AdminDestinationMap).where(
            AdminDestinationMap.admin_id == admin.id,
            AdminDestinationMap.destination_id == destination_id
        )
        is_authorized = (await session.execute(q)).scalar_one_or_none()

        if not is_authorized:
            await query.answer("شما مجوز مدیریت این مقصد را ندارید.", show_alert=True)
            logging.warning(f"Unauthorized access attempt by admin {user.id} for destination {destination_id}")
            return

        article = await session.get(Article, article_id)
        if not article:
            await query.edit_message_text(text="خطا: مقاله یافت نشد.")
            return

        if action == 'approve':
            rabbit_client = get_rabbit_client()
            message = {
                "article_id": article_id,
                "destination_id": destination_id
            }
            await rabbit_client.publish(
                exchange='ex.articles',
                routing_key='rk.publication_approved',
                body=json.dumps(message)
            )
            await query.edit_message_text(text=f"✅ مقاله برای انتشار در این مقصد تایید شد.\n\n{query.message.text}")
        
        elif action == 'reject':
            if article.assigned_destinations:
                # Remove the rejected destination from the list
                article.assigned_destinations = [d for d in article.assigned_destinations if d.get("destination_id") != destination_id]
                if not article.assigned_destinations: # If no destinations are left
                    article.status = ArticleStatus.REJECTED
                await session.commit()
            await query.edit_message_text(text=f"❌ انتشار مقاله برای این مقصد رد شد.\n\n{query.message.text}")

# This function is called by the RabbitMQ consumer
async def send_approval_request(db_session_factory, bot, article_id: int):
    async with db_session_factory() as session:
        article = await session.get(Article, article_id)
        if not article or not article.assigned_destinations:
            return

        for dest_info in article.assigned_destinations:
            dest_id = dest_info['destination_id']
            # Find admins for this destination
            q = select(Admin.telegram_id).join(AdminDestinationMap).where(AdminDestinationMap.destination_id == dest_id)
            admin_telegram_ids = (await session.execute(q)).scalars().all()
            
            dest = await session.get(Destination, dest_id)

            for tid in set(admin_telegram_ids):
                keyboard = [
                    [
                        InlineKeyboardButton("✅ تایید انتشار", callback_data=f"approve:{article_id}:{dest_id}"),
                        InlineKeyboardButton("❌ رد کردن", callback_data=f"reject:{article_id}:{dest_id}"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = (f"👇🏼 درخواست تایید محتوای جدید برای مقصد '{dest.name} - {dest.platform.value}'\n\n"
                        f"**عنوان:** {article.processed_title}\n\n"
                        f"**لینک اصلی:** {article.original_url}")
                try:
                    await bot.send_message(chat_id=tid, text=text, reply_markup=reply_markup, parse_mode='Markdown')
                except Exception as e:
                    logging.error(f"Failed to send message to admin {tid}: {e}")