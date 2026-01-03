import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from auth import restricted
from encryption import security
from dotenv import load_dotenv

# Managers
from playlist_manager import playlist_manager
from key_manager import key_manager
from stream_manager import stream_manager

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
BOT_TOKEN = security.decrypt(TOKEN_ENCRYPTED) or os.getenv('LIVEXA_BOT_TOKEN_PLAIN')

if not BOT_TOKEN:
     print("CRITICAL: No Bot Token found.")
     sys.exit(1)

# Conversation States
(
    WAITING_PLAYLIST_NAME,
    WAITING_STREAM_KEY_ALIAS,
    WAITING_STREAM_KEY_VALUE,
    w, # Placeholders if needed
) = range(4)

# --- KEYBOARDS ---

def main_menu_keyboard(chat_id):
    status = stream_manager.get_status(chat_id)
    stream_text = "⏹ Stream Offline" if not status else f"🔴 LIVE ({status['uptime']}s)"
    
    keyboard = [
        [InlineKeyboardButton("▶ Start Stream", callback_data='menu_start_flow'),
         InlineKeyboardButton("⏹ Stop Stream", callback_data='menu_stop')],
        [InlineKeyboardButton("📂 My Playlists", callback_data='menu_playlists'),
         InlineKeyboardButton("🔑 Stream Keys", callback_data='menu_keys')],
        [InlineKeyboardButton("📊 Status", callback_data='menu_status')]
    ]
    return InlineKeyboardMarkup(keyboard), stream_text

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data='cancel_op')]])

# --- COMMAND HANDLERS ---

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    kb, status = main_menu_keyboard(update.effective_chat.id)
    await update.message.reply_html(
        rf"👋 <b>Livexa V2 Operations</b>" + "\n\n" +
        f"<b>Status:</b> {status}\n" + 
        "Control Center active. Select an action:",
        reply_markup=kb
    )

@restricted
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Livexa - Enterprise Automation V2</b>\n"
        "---------------------------------\n"
        "<b>Author:</b> Yogeshwar Kumar\n"
        "<b>GitHub:</b> https://github.com/inyogeshwar\n"
        "---------------------------------"
    )
    await update.message.reply_html(text)

# --- FLOWS: START STREAM ---

@restricted
async def start_flow_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    # Check running
    if stream_manager.get_status(chat_id):
        await query.edit_message_text("⚠️ <b>Stream is already LIVE!</b> Stop it first.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='main_menu')]]))
        return

    # 1. Select Playlist
    playlists = playlist_manager.list_playlists(chat_id)
    if not playlists:
        await query.edit_message_text("❌ <b>No Playlists Found.</b>\nGo to 'My Playlists' to create one.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='main_menu')]]))
        return
        
    buttons = [[InlineKeyboardButton(f"📂 {p}", callback_data=f"sel_pl_{p}")] for p in playlists]
    buttons.append([InlineKeyboardButton("« Cancel", callback_data='main_menu')])
    await query.edit_message_text("<b>Step 1/2:</b> Select a Playlist for this stream:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def select_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    playlist_name = query.data.replace("sel_pl_", "")
    # Verify validity
    if not playlist_manager.get_concat_file_path(chat_id, playlist_name):
        await query.edit_message_text("❌ Playlist invalid (empty?).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='menu_start_flow')]]))
        return

    # Store choice in user_data
    context.user_data['temp_start_playlist'] = playlist_name
    
    # 2. Select Key
    keys = key_manager.list_keys(chat_id)
    if not keys:
        await query.edit_message_text("❌ <b>No Stream Keys Found.</b>\nGo to 'Stream Keys' to add one.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='main_menu')]]))
        return

    buttons = [[InlineKeyboardButton(f"🔑 {k}", callback_data=f"sel_key_{k}")] for k in keys]
    buttons.append([InlineKeyboardButton("« Back", callback_data='menu_start_flow')])
    await query.edit_message_text(f"<b>Step 2/2:</b> Playlist: <i>{playlist_name}</i>\nSelect Stream Key:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def select_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    key_alias = query.data.replace("sel_key_", "")
    playlist_name = context.user_data.get('temp_start_playlist')
    
    # Retrieve actual secret
    stream_key = key_manager.get_key(chat_id, key_alias)
    concat_path = playlist_manager.get_concat_file_path(chat_id, playlist_name)
    
    if not stream_key or not concat_path:
        await query.edit_message_text("❌ Error resolving resources.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Main Menu", callback_data='main_menu')]]))
        return
        
    # START
    await query.edit_message_text(f"🟡 <b>Connecting to YouTube...</b>\nPlaylist: {playlist_name}\nKey: {key_alias}", parse_mode=ParseMode.HTML)
    
    success = stream_manager.start_stream(chat_id, stream_key, key_alias, concat_path, playlist_name)
    
    if success:
         kb, status = main_menu_keyboard(chat_id)
         await query.edit_message_text(f"✅ <b>SUCCESS: Stream is LIVE!</b>\n{status}", parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
         await query.edit_message_text("❌ <b>FAILED to start stream.</b> Check logs.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Main Menu", callback_data='main_menu')]]))

@restricted
async def stop_stream_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    stopped = stream_manager.stop_stream(chat_id)
    msg = "⏹ <b>Stream Stopped Successfully.</b>" if stopped else "⚠️ No active stream found."
    
    kb, _ = main_menu_keyboard(chat_id)
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)

# --- PLAYLIST MANAGEMENT FLOW ---

@restricted
async def menu_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    playlists = playlist_manager.list_playlists(chat_id)
    buttons = []
    for p in playlists:
        # Show file count
        count = len(playlist_manager.get_playlist_files(chat_id, p))
        buttons.append([InlineKeyboardButton(f"📂 {p} ({count} files)", callback_data=f"manage_pl_{p}")])
    
    buttons.append([InlineKeyboardButton("➕ Create New Playlist", callback_data='create_playlist_start')])
    buttons.append([InlineKeyboardButton("« Back", callback_data='main_menu')])
    
    await query.edit_message_text("<b>📂 Playlist Manager</b>\nSelect one to manage or upload media:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def manage_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    p_name = query.data.replace("manage_pl_", "")
    
    # Store selected playlist in context for Uploads
    context.user_data['selected_playlist'] = p_name
    
    files = playlist_manager.get_playlist_files(chat_id, p_name)
    file_list = "\n".join([f"- {f}" for f in files[:10]]) # Limit display
    if len(files) > 10: file_list += f"\n...and {len(files)-10} more"
    
    text = f"<b>Managing: {p_name}</b>\n\nFile List:\n{file_list or '(Empty)'}\n\n<b>To Upload Media:</b>\nJust send MP3/MP4/Images to this chat NOW."
    
    buttons = [
        [InlineKeyboardButton("❌ Delete Specific Files", callback_data=f"del_files_menu_{p_name}")],
        [InlineKeyboardButton("🗑 Delete Playlist", callback_data=f"del_pl_confirm_{p_name}")],
        [InlineKeyboardButton("« Back to Playlists", callback_data='menu_playlists')]
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def del_files_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    p_name = query.data.replace("del_files_menu_", "")
    
    files = playlist_manager.get_playlist_files(chat_id, p_name)
    if not files:
        await query.edit_message_text("Folder is empty.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data=f"manage_pl_{p_name}")]]))
        return

    buttons = []
    for f in files:
        buttons.append([InlineKeyboardButton(f"🗑 {f}", callback_data=f"del_file_confirm_{p_name}|{f}")])
    
    buttons.append([InlineKeyboardButton("« Back", callback_data=f"manage_pl_{p_name}")])
    await query.edit_message_text(f"<b>Delete File from '{p_name}':</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def del_file_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.replace("del_file_confirm_", "")
    p_name, f_name = data.split("|", 1)
    chat_id = update.effective_chat.id
    
    if playlist_manager.remove_file(chat_id, p_name, f_name):
        await query.answer(f"Deleted {f_name}")
    else:
        await query.answer("Failed to delete.")
        
    # Refresh list
    await del_files_menu_callback(update, context)

@restricted
async def create_playlist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("<b>Enter name for new playlist:</b>", parse_mode=ParseMode.HTML)
    return WAITING_PLAYLIST_NAME

@restricted
async def create_playlist_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().replace(" ", "_") # Simple sanitation
    chat_id = update.effective_chat.id
    
    if playlist_manager.create_playlist(chat_id, name):
        await update.message.reply_text(f"✅ Playlist '{name}' created!")
    else:
        await update.message.reply_text(f"❌ Failed. '{name}' might already exist.")
    
    # Return to menu UI
    kb, _ = main_menu_keyboard(chat_id)
    await update.message.reply_text("Control Panel:", reply_markup=kb)
    return ConversationHandler.END

@restricted
async def delete_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    p_name = query.data.replace("del_pl_confirm_", "")
    chat_id = update.effective_chat.id
    
    playlist_manager.delete_playlist(chat_id, p_name)
    await query.answer(f"Playlist {p_name} deleted.")
    # Return to list
    await menu_playlists(update, context)

# --- MEDIA UPLOAD HANDLER ---

@restricted
async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    selected_playlist = context.user_data.get('selected_playlist')
    
    if not selected_playlist:
        await update.message.reply_text("⚠️ <b>No Playlist Selected.</b>\nGo to 'My Playlists' -> Select one -> Then upload.", parse_mode=ParseMode.HTML)
        return

    # Check file
    doc = update.message.document or update.message.audio or update.message.video
    if not doc:
        return # Should catch photo handling logic too if needed

    file_name = doc.file_name or f"file_{doc.file_unique_id}"
    mime = doc.mime_type
    
    msg = await update.message.reply_text(f"⏳ Downloading {file_name}...")
    
    try:
        new_file = await doc.get_file()
        byte_data = await new_file.download_as_bytearray()
        
        playlist_manager.add_file(chat_id, selected_playlist, file_name, byte_data)
        await msg.edit_text(f"✅ Saved to <b>{selected_playlist}</b>", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await msg.edit_text(f"❌ Upload failed: {e}")

# --- KEY MANAGEMENT FLOW ---

@restricted
async def menu_keys(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    keys = key_manager.list_keys(chat_id)
    text = "<b>🔑 Stream Key Manager</b>\nSaved Keys:\n" + ("\n".join(keys) if keys else "(None)")
    
    buttons = [
        [InlineKeyboardButton("➕ Add New Key", callback_data='add_key_start')],
        [InlineKeyboardButton("🗑 Delete Key", callback_data='del_key_menu')],
        [InlineKeyboardButton("« Back", callback_data='main_menu')]
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@restricted
async def add_key_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("<b>Enter an ALIAS (Name) for this key:</b>\n(e.g., 'MainChannel', 'Gaming')", parse_mode=ParseMode.HTML)
    return WAITING_STREAM_KEY_ALIAS

@restricted
async def add_key_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alias = update.message.text.strip()
    context.user_data['new_key_alias'] = alias
    await update.message.reply_text("<b>Enter the ACTUAL Stream Key:</b>\n(It will be encrypted immediately)", parse_mode=ParseMode.HTML)
    return WAITING_STREAM_KEY_VALUE

@restricted
async def add_key_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_val = update.message.text.strip()
    alias = context.user_data['new_key_alias']
    chat_id = update.effective_chat.id
    
    key_manager.add_key(chat_id, alias, key_val)
    
    # Delete the message containing the key for security
    try:
        await update.message.delete()
    except:
        pass
        
    await update.message.reply_text(f"✅ Key '{alias}' saved securely!", reply_markup=main_menu_keyboard(chat_id)[0])
    return ConversationHandler.END

# --- GENERIC NAVIGATION ---

@restricted
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb, status = main_menu_keyboard(update.effective_chat.id)
    await query.edit_message_text(f"<b>Status:</b> {status}\nControl Center:", parse_mode=ParseMode.HTML, reply_markup=kb)

# --- MAIN SETUP ---

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation Handlers
    playlist_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_playlist_start, pattern='^create_playlist_start$')],
        states={WAITING_PLAYLIST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_playlist_finish)]},
        fallbacks=[CommandHandler('cancel', start)]
    )

    key_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_key_step1, pattern='^add_key_start$')],
        states={
            WAITING_STREAM_KEY_ALIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_step2)],
            WAITING_STREAM_KEY_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_finish)],
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    # Global Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    
    # Converstations
    application.add_handler(playlist_conv)
    application.add_handler(key_conv)
    
    # Document Uploads (Global but logic checks context)
    application.add_handler(MessageHandler(filters.ATTACHMENT, handle_document_upload))

    # Menu Callbacks
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(menu_playlists, pattern='^menu_playlists$'))
    application.add_handler(CallbackQueryHandler(menu_keys, pattern='^menu_keys$'))
    application.add_handler(CallbackQueryHandler(start_flow_entry, pattern='^menu_start_flow$'))
    application.add_handler(CallbackQueryHandler(stop_stream_callback, pattern='^menu_stop$'))
    application.add_handler(CallbackQueryHandler(select_playlist_callback, pattern='^sel_pl_'))
    application.add_handler(CallbackQueryHandler(select_key_callback, pattern='^sel_key_'))
    application.add_handler(CallbackQueryHandler(manage_playlist_callback, pattern='^manage_pl_'))
    application.add_handler(CallbackQueryHandler(delete_playlist_callback, pattern='^del_pl_confirm_'))
    application.add_handler(CallbackQueryHandler(del_files_menu_callback, pattern='^del_files_menu_'))
    application.add_handler(CallbackQueryHandler(del_file_confirm_callback, pattern='^del_file_confirm_'))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
