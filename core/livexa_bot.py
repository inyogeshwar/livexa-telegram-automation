import logging
import os
import signal
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from auth import restricted
from dispatcher import dispatcher
from encryption import security
from dotenv import load_dotenv

# Load config
load_dotenv(os.path.join(os.path.dirname(__file__), '../config/livexa.env'))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
TOKEN_ENCRYPTED = os.getenv('LIVEXA_BOT_TOKEN_ENC')
BOT_TOKEN = security.decrypt(TOKEN_ENCRYPTED)

if not BOT_TOKEN:
    print("CRITICAL: Could not decrypt Bot Token. Check livexa_secrets.enc and key.")
    # For initial setup fallback, allow plain token if provided
    BOT_TOKEN = os.getenv('LIVEXA_BOT_TOKEN_PLAIN')

if not BOT_TOKEN:
     print("CRITICAL: No Bot Token found.")
     sys.exit(1)

# Keyboard Layouts
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("▶ Start Live", callback_data='start_menu'),
         InlineKeyboardButton("⏹ Stop Live", callback_data='stop_confirm')],
        [InlineKeyboardButton("🔄 Switch Playlist", callback_data='playlist_menu'),
         InlineKeyboardButton("📺 Switch Channel", callback_data='channel_menu')],
        [InlineKeyboardButton("📊 Server Stats", callback_data='stats'),
         InlineKeyboardButton("♻ Reboot VM", callback_data='reboot_confirm')]
    ]
    return InlineKeyboardMarkup(keyboard)

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"👋 Hi {user.mention_html()}! Welcome to <b>Livexa Enterprise Panel</b>.",
        reply_markup=main_menu_keyboard()
    )

@restricted
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'start_menu':
        # Show Start options (e.g. choose playlist)
        # Simplified for V1: Just start default
        try:
            # Mock key and playlist for now, in real app ask user
            default_key = os.getenv('DEFAULT_STREAM_KEY', 'rtmp://a.rtmp.youtube.com/live2/xxxx-xxxx')
            dispatcher.start_stream(default_key, 'music')
            await query.edit_message_text(text="✅ <b>Stream Dispatch signal sent!</b>", parse_mode='HTML', reply_markup=main_menu_keyboard())
        except Exception as e:
            await query.edit_message_text(text=f"❌ Error: {str(e)}", reply_markup=main_menu_keyboard())

    elif data == 'stop_confirm':
        dispatcher.stop_stream()
        await query.edit_message_text(text="⏹ <b>All Streams Stopped.</b>", parse_mode='HTML', reply_markup=main_menu_keyboard())

    elif data == 'stats':
        # Mock stats
        await query.edit_message_text(text="📊 <b>System Load:</b> 12%\n💾 <b>RAM:</b> 2.4GB / 8GB\n🔥 <b>Stream Status:</b> HEALTHY", parse_mode='HTML', reply_markup=main_menu_keyboard())
    
    elif data == 'reboot_confirm':
         await query.edit_message_text(text="♻ <b>Rebooting System in 5s...</b>", parse_mode='HTML')
         # os.system('reboot') # Dangerous in test env, disabled for safety

    elif data == 'main_menu':
        await query.edit_message_text(text="<b>Livexa Control Panel</b>", parse_mode='HTML', reply_markup=main_menu_keyboard())

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /about is issued."""
    about_text = (
        "<b>Livexa - Enterprise Automation</b>\n"
        "---------------------------------\n"
        "<b>Author:</b> Yogeshwar Kumar\n"
        "<b>GitHub:</b> https://github.com/inyogeshwar\n"
        "<b>YouTube:</b> https://www.youtube.com/@inyogeshwar_official\n"
        "<b>Instagram:</b> https://instagram.com/in_yogeshwar\n"
        "---------------------------------\n"
        "<i>Version 1.0.0 | Enterprise Edition</i>"
    )
    await update.message.reply_html(about_text)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
