import os
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# Load Admin IDs as a set of integers
ADMIN_IDS = set()
raw_ids = os.getenv('LIVEXA_ADMIN_IDS', '')
if raw_ids:
    ADMIN_IDS = {int(x.strip()) for x in raw_ids.split(',') if x.strip().isdigit()}

def restricted(func):
    """
    Decorator to restrict usage of bot commands to authorized admins.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            print(f"WARNING: Unauthorized access attempt by {user_id}")
            # Optional: Notify admin or just ignore
            if update.message:
                await update.message.reply_text("⛔ Unauthorized Access.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Unauthorized Access.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
