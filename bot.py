# ========================================================================
# LIVEXABOT: PREMIUM SINGLE-LIVE YOUTUBE STREAMING
# Version: 2.0 (FINAL) • Simplified UI • Interactive Buttons • 1080p
# ========================================================================

import os
import signal
import subprocess
import json
import asyncio
import logging
import time
from pathlib import Path

import psutil
import gdown
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ------------------------------------------------------------------------
# CONFIG & DIRECTORIES
# ------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
if not BOT_TOKEN:
    BOT_TOKEN = "PASTE_YOUR_TOKEN_HERE" 

BASE = Path("/opt/livexa")
STORAGE = BASE / "storage"
MEDIA_DIR = STORAGE / "media"
MEDIA_DIR.mkdir(exist_ok=True, parents=True)
CONFIG_FILE = STORAGE / "config.json"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("LivexaBot")

ADMIN_ID = None 
USER_STATE = {} # Tracking interaction state (e.g. 'awaiting_key')

# ------------------------------------------------------------------------
# DATA PERSISTENCE
# ------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "key": None,
    "quality": "720p",
    "mode": "video",
    "pid": None
}

def load_config():
    if not CONFIG_FILE.exists(): return DEFAULT_CONFIG
    try:
        data = json.loads(CONFIG_FILE.read_text())
        pid = data.get("pid")
        if pid and not psutil.pid_exists(pid):
            data["pid"] = None # Reset dead PID
        return data
    except: return DEFAULT_CONFIG

def save_config(config):
    try: CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except: pass

CONFIG = load_config()

# ------------------------------------------------------------------------
# UI UTILS
# ------------------------------------------------------------------------
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🚀 Start Live"), KeyboardButton("⏹ Stop Live")],
        [KeyboardButton("🔑 Set Key"), KeyboardButton("🔗 Set Source")],
        [KeyboardButton("🎬 Change Mode"), KeyboardButton("📊 Status")],
        [KeyboardButton("⚙️ Quality")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_inline_menu():
    keyboard = [
        [InlineKeyboardButton("🚀 Go Live", callback_data="start_live"), InlineKeyboardButton("⏹ Stop", callback_data="stop_live")],
        [InlineKeyboardButton("📊 System Status", callback_data="status_check")],
        [InlineKeyboardButton("🛠 Setup Instructions", callback_data="show_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_only(update: Update):
    global ADMIN_ID
    uid = update.effective_user.id
    if ADMIN_ID is None: ADMIN_ID = uid
    return uid == ADMIN_ID

# ------------------------------------------------------------------------
# CORE HANDLERS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    await update.message.reply_text(
        "🎬 **LIVEXABOT PREMIUM V2.0**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome! Your single-stream control center is ready.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await update.message.reply_text("Tap below to manage your stream:", reply_markup=get_inline_menu())

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "🚀 Start Live": return await start_live_logic(update)
    if text == "⏹ Stop Live": return await stop_live_logic(update)
    if text == "📊 Status": return await status_logic(update)
    
    if text == "🔑 Set Key":
        USER_STATE[chat_id] = "awaiting_key"
        return await update.message.reply_text("👉 **YouTube Stream Key** bhejiye ya type karein:", parse_mode="Markdown")
    
    if text == "🔗 Set Source":
        USER_STATE[chat_id] = "awaiting_source"
        return await update.message.reply_text("👉 **Google Drive Link** bhejiye:", parse_mode="Markdown")
    
    if text == "🎬 Change Mode":
        return await update.message.reply_text("👉 Type: `/mode video|radio|overlay`", parse_mode="Markdown")
    
    if text == "⚙️ Quality":
        return await update.message.reply_text("👉 Type: `/quality 1080p|720p|360p`", parse_mode="Markdown")

async def state_and_upload_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    msg = update.message
    chat_id = update.effective_chat.id
    state = USER_STATE.get(chat_id)

    # 1. State-Based Text Entry
    if msg.text and state:
        if state == "awaiting_key":
            CONFIG["key"] = msg.text.strip()
            save_config(CONFIG)
            USER_STATE.pop(chat_id)
            return await msg.reply_text(f"✅ **Key Saved!**\n`{CONFIG['key']}`", parse_mode="Markdown")
        
        if state == "awaiting_source":
            USER_STATE.pop(chat_id)
            ctx.args = [msg.text.strip()]
            return await source_cmd(update, ctx)

    # 2. Direct File Uploads
    if msg.photo or msg.video or msg.audio or msg.document:
        await handle_file_upload(update)
        return

    # Fallback to Text Button Handler
    if msg.text:
        await button_handler(update, ctx)

async def handle_file_upload(update: Update):
    msg = update.message
    # Image
    if msg.photo:
        await (await msg.photo[-1].get_file()).download_to_drive(MEDIA_DIR / "image.jpg")
        return await msg.reply_text("🖼 **Image Updated!**", parse_mode="Markdown")
    
    media = msg.video or msg.audio or msg.document
    if not media: return
    
    fname = (media.file_name or "").lower()
    if msg.video or fname.endswith(".mp4"):
        await (await media.get_file()).download_to_drive(MEDIA_DIR / "video.mp4")
        if CONFIG["mode"] == "radio": 
            CONFIG["mode"] = "video"
            save_config(CONFIG)
        return await msg.reply_text("📹 **Video Updated!** (Mode auto-set to Video)", parse_mode="Markdown")
    
    if msg.audio or fname.endswith(".mp3"):
        await (await media.get_file()).download_to_drive(MEDIA_DIR / "audio.mp3")
        return await msg.reply_text("🎵 **Audio Updated!**", parse_mode="Markdown")

# ------------------------------------------------------------------------
# ACTION LOGIC
# ------------------------------------------------------------------------
async def start_live_logic(update: Update):
    if CONFIG.get("pid") and psutil.pid_exists(CONFIG["pid"]):
        return await update.message.reply_text("⚠️ Already running.")
    if not CONFIG.get("key"):
        return await update.message.reply_text("❌ Key missing. Click 'Set Key' first.")

    img, aud, vid = MEDIA_DIR / "image.jpg", MEDIA_DIR / "audio.mp3", MEDIA_DIR / "video.mp4"
    mode = CONFIG.get("mode", "video")

    if mode == "video" and not vid.exists(): return await update.message.reply_text("❌ Video file (video.mp4) missing.")
    if mode == "radio" and (not img.exists() or not aud.exists()):
         return await update.message.reply_text("❌ Radio mode requires Image + Audio.")
    if mode == "overlay" and (not vid.exists() or not aud.exists()):
         return await update.message.reply_text("❌ Overlay mode requires Video + Audio.")

    q_map = {"360p": ("640:360","800k","128k"), "720p": ("1280:720","2500k","192k"), "1080p": ("1920:1080","4500k","256k")}
    res, bv, ba = q_map.get(CONFIG["quality"], q_map["720p"])
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{CONFIG['key']}"

    cmd = ["ffmpeg", "-re"]
    if mode == "video": cmd += ["-stream_loop", "-1", "-i", str(vid)]
    elif mode == "radio": cmd += ["-loop", "1", "-i", str(img), "-stream_loop", "-1", "-i", str(aud)]
    elif mode == "overlay": cmd += ["-stream_loop", "-1", "-i", str(vid), "-stream_loop", "-1", "-i", str(aud), "-map", "0:v", "-map", "1:a", "-shortest"]
    
    cmd += ["-vf", f"scale={res},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-b:v", bv, "-maxrate", bv, "-bufsize", "5000k", "-g", "60", "-c:a", "aac", "-b:a", ba, "-ar", "44100", "-f", "flv", rtmp]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        await asyncio.sleep(3)
        if proc.poll() is not None:
             _, err = proc.communicate()
             return await update.message.reply_text(f"❌ Failed: `{err.decode()[-200:]}`")
        CONFIG["pid"] = proc.pid
        save_config(CONFIG)
        await update.message.reply_text(f"🚀 **LIVE STARTED!**\nMode: `{mode}` | Quality: `{res}`", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")

async def stop_live_logic(update: Update):
    pid = CONFIG.get("pid")
    if not pid or not psutil.pid_exists(pid):
        return await update.message.reply_text("💤 Not running.")
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        await update.message.reply_text("⏹ **Stopped!**", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Process was already ending.")
    CONFIG["pid"] = None
    save_config(CONFIG)

async def status_logic(update: Update):
    pid = CONFIG.get("pid")
    alive = pid and psutil.pid_exists(pid)
    await update.message.reply_text(
        f"📊 **SYSTEM STATUS**\n"
        f"━━━━━━━━━━━━━━\n"
        f"State: {'🟢 ONLINE' if alive else '💤 IDLE'}\n"
        f"Mode: `{CONFIG['mode']}`\n"
        f"Quality: `{CONFIG['quality']}`\n"
        f"Key: `{'SET ✅' if CONFIG['key'] else 'NOT SET ❌'}`",
        parse_mode="Markdown"
    )

# ------------------------------------------------------------------------
# CMD WRAPPERS
# ------------------------------------------------------------------------
async def source_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/source <url>`")
    url = ctx.args[0]
    msg = await update.message.reply_text("⏳ **Downloading...**", parse_mode="Markdown")
    try:
        temp = MEDIA_DIR / f"dl_{int(time.time())}"
        out = await asyncio.to_thread(gdown.download, url, str(temp), quiet=True, fuzzy=True)
        if not out: return await msg.edit_text("❌ Download failed.")
        o_path = Path(out)
        ext = o_path.suffix.lower()
        if ext in [".mp4", ".mkv", ".mov"]:
            target, mode, txt = MEDIA_DIR / "video.mp4", "video", "📹 Video set!"
        elif ext in [".mp3", ".wav", ".m4a"]:
            target, mode, txt = MEDIA_DIR / "audio.mp3", None, "🎵 Audio set!"
        elif ext in [".jpg", ".jpeg", ".png"]:
            target, mode, txt = MEDIA_DIR / "image.jpg", None, "🖼 Image set!"
        else:
            is_vid = o_path.stat().st_size > 5*1024*1024
            target, mode, txt = (MEDIA_DIR / "video.mp4", "video", "📹 Video set!") if is_vid else (MEDIA_DIR / "audio.mp3", None, "🎵 Audio set!")
        
        if target.exists(): target.unlink()
        o_path.rename(target)
        if mode: 
            CONFIG["mode"] = mode
            save_config(CONFIG)
        await msg.edit_text(f"✅ **{txt}**", parse_mode="Markdown")
    except Exception as e: await msg.edit_text(f"❌ Error: {e}")

async def mode_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/mode video|radio|overlay`")
    m = ctx.args[0].lower()
    if m in ["video", "radio", "overlay"]:
        CONFIG["mode"] = m
        save_config(CONFIG)
        await update.message.reply_text(f"✅ Mode set to `{m}`")
    else:
        await update.message.reply_text("❌ Invalid mode.")

async def quality_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/quality 1080p|720p|360p`")
    q = ctx.args[0].lower()
    if q in ["1080p", "720p", "360p"]:
        CONFIG["quality"] = q
        save_config(CONFIG)
        await update.message.reply_text(f"✅ Quality set to `{q}`")
    else:
        await update.message.reply_text("❌ Invalid quality.")

async def inline_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_live": await start_live_logic(query)
    elif query.data == "stop_live": await stop_live_logic(query)
    elif query.data == "status_check": await status_logic(query)
    elif query.data == "show_help":
        await query.message.reply_text("📖 **Quick Start:**\n1. Set Key button\n2. Set Source button (GDrive) or upload file\n3. Start Live 🚀", parse_mode="Markdown")

# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
def main():
    print("🤖 LivexaBot Premium V2.0 Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("quality", quality_cmd))
    app.add_handler(CommandHandler("source", source_cmd))
    app.add_handler(CommandHandler("setkey", lambda u, c: button_handler(u, c) if u.message.text == "🔑 Set Key" else None)) # Dummy for help
    
    app.add_handler(CallbackQueryHandler(inline_callback))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), state_and_upload_handler))
    
    app.run_polling()

if __name__ == "__main__": main()
