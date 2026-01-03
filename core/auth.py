from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from admin_manager import admin_manager

def restricted(func):
    """
    Decorator to restrict usage to dynamically managed admins.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Handle different update types
        user = None
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        elif update.effective_user:
            user = update.effective_user
            
        if not user:
            return # Should not happen usually

        if not admin_manager.is_admin(user.id):
            print(f"WARNING: Unauthorized access attempt by {user.id} ({user.username})")
            # Silent ignore or simple alert if it's a direct message
            if update.message:
                # Optional: Reply for UX, or silent for security. V3 Req says silent/ignore
                pass 
            elif update.callback_query:
                await update.callback_query.answer("⛔ Unauthorized", show_alert=True)
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped
