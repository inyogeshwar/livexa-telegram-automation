# ========================================================================
# LIVEXABOT: PROFESSIONAL SINGLE-LIVE (CONTAINER-READY)
# Version: 2.3 (UNIVERSAL) • Pterodactyl Ready • Env-Driven • 1080p
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
# DYNAMIC PATHS (PTERODACTYL & DOCKER COMPATIBLE)
# ------------------------------------------------------------------------
# If running in Pterodactyl, use /home/container. Otherwise, fallback to /opt or local.
if Path("/home/container").exists():
    BASE = Path("/home/container")
elif Path("/opt/livexa").exists() or os.access("/opt", os.W_OK):
    BASE = Path("/opt/livexa")
    BASE.mkdir(exist_ok=True, parents=True)
else:
    BASE = Path.cwd()

STORAGE = BASE / "storage"
STORAGE.mkdir(exist_ok=True, parents=True)

MEDIA_DIR = STORAGE / "media"
MEDIA_DIR.mkdir(exist_ok=True, parents=True)

CONFIG_FILE = STORAGE / "config.json"

# ------------------------------------------------------------------------
# LOGGING (CONSOLE-FIRST FOR PANEL)
# ------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("LivexaBot")

# ------------------------------------------------------------------------
# CONFIG & TOKEN
# ------------------------------------------------------------------------
# Prioritize Environment Variables (Set in Pterodactyl/Docker)
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
if not BOT_TOKEN:
    # Try local config if no env var
    BOT_TOKEN = "PASTE_YOUR_TOKEN_HERE" 

ADMIN_ID = os.environ.get("ADMIN_ID") # Optional lock
USER_STATE = {} 

# ------------------------------------------------------------------------
# DATA PERSISTENCE
# ------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "key": os.environ.get("STREAM_KEY"),
    "quality": os.environ.get("QUALITY", "720p"),
    "mode": "video",
    "pid": None
}

def load_config():
    if not CONFIG_FILE.exists(): return DEFAULT_CONFIG
    try:
        data = json.loads(CONFIG_FILE.read_text())
        pid = data.get("pid")
        if pid and not psutil.pid_exists(pid):
            data["pid"] = None
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
    if ADMIN_ID is None:
        # First person to message becomes Admin if not set in Env
        ADMIN_ID = uid
        logger.info(f"Admin set to: {ADMIN_ID}")
    return str(uid) == str(ADMIN_ID)

# ------------------------------------------------------------------------
# CORE HANDLERS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    await update.message.reply_text(
        "🎬 **LIVEXABOT MASTER PANEL (V2.3)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Professional Control Dashboard is Online.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await update.message.reply_text("Interacting via Pterodactyl environment ✅", reply_markup=get_inline_menu())

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "🚀 Start Live": return await start_live_logic(update)
    if text == "⏹ Stop Live": return await stop_live_logic(update)
    if text == "📊 Status": return await status_logic(update)
    
    if text == "🔑 Set Key":
        USER_STATE[chat_id] = "awaiting_key"
        return await update.message.reply_text("👉 **YouTube Stream Key** bhejiye:", parse_mode="Markdown")
    
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

    if msg.text and state:
        if state == "awaiting_key":
            CONFIG["key"] = msg.text.strip()
            save_config(CONFIG)
            USER_STATE.pop(chat_id)
            return await msg.reply_text(f"✅ **Key Saved!**", parse_mode="Markdown")
        if state == "awaiting_source":
            USER_STATE.pop(chat_id)
            ctx.args = [msg.text.strip()]
            return await source_cmd(update, ctx)

    if msg.photo or msg.video or msg.audio or msg.document:
        await handle_file_upload(update)
        return

    if msg.text:
        await button_handler(update, ctx)

async def handle_file_upload(update: Update):
    msg = update.message
    if msg.photo:
        await (await msg.photo[-1].get_file()).download_to_drive(MEDIA_DIR / "image.jpg")
        return await msg.reply_text("🖼 **Image Updated!**")
    
    media = msg.video or msg.audio or msg.document
    if not media: return
    
    fname = (media.file_name or "").lower()
    if msg.video or fname.endswith(".mp4"):
        await (await media.get_file()).download_to_drive(MEDIA_DIR / "video.mp4")
        if CONFIG["mode"] == "radio": 
            CONFIG["mode"] = "video"
            save_config(CONFIG)
        return await msg.reply_text("📹 **Video Updated!**")
    if msg.audio or fname.endswith(".mp3"):
        await (await media.get_file()).download_to_drive(MEDIA_DIR / "audio.mp3")
        return await msg.reply_text("🎵 **Audio Updated!**")

# ------------------------------------------------------------------------
# ACTION LOGIC
# ------------------------------------------------------------------------
async def start_live_logic(update: Update):
    # (Existing start logic, same but using MEDIA_DIR)
    if CONFIG.get("pid") and psutil.pid_exists(CONFIG["pid"]):
        return await update.message.reply_text("⚠️ Already running.")
    if not CONFIG.get("key"):
        return await update.message.reply_text("❌ Key missing.")

    img, aud, vid = MEDIA_DIR / "image.jpg", MEDIA_DIR / "audio.mp3", MEDIA_DIR / "video.mp4"
    mode = CONFIG.get("mode", "video")

    if mode == "video" and not vid.exists(): return await update.message.reply_text("❌ Missing video.mp4")
    if mode == "radio" and (not img.exists() or not aud.exists()): return await update.message.reply_text("❌ Missing Img/Audio")
    if mode == "overlay" and (not vid.exists() or not aud.exists()): return await update.message.reply_text("❌ Missing Vid/Audio")

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
             return await update.message.reply_text("❌ FFmpeg failed to start.")
        CONFIG["pid"] = proc.pid
        save_config(CONFIG)
        await update.message.reply_text(f"🚀 **LIVE STARTED!**\nMode: `{mode}` | Quality: `{res}`", parse_mode="Markdown")
        logger.info("Stream started successfully.")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")

async def stop_live_logic(update: Update):
    pid = CONFIG.get("pid")
    if pid and psutil.pid_exists(pid):
        try: os.killpg(os.getpgid(pid), signal.SIGTERM)
        except: pass
    CONFIG["pid"] = None
    save_config(CONFIG)
    await update.message.reply_text("⏹ **Stopped!**")

async def status_logic(update: Update):
    alive = CONFIG.get("pid") and psutil.pid_exists(CONFIG["pid"])
    await update.message.reply_text(f"📊 **STATUS**\nLive: {'🟢' if alive else '💤'}\nMode: `{CONFIG['mode']}`\nQuality: `{CONFIG['quality']}`", parse_mode="Markdown")

# ------------------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------------------
async def source_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args: return
    url = ctx.args[0]
    m = await update.message.reply_text("⏳ **Downloading...**", parse_mode="Markdown")
    try:
        temp = MEDIA_DIR / f"dl_{int(time.time())}"
        out = await asyncio.to_thread(gdown.download, url, str(temp), quiet=True, fuzzy=True)
        if not out: return await m.edit_text("❌ Failed.")
        o_path, ext = Path(out), Path(out).suffix.lower()
        if ext in [".mp4", ".mkv", ".mov"]: target, mode = MEDIA_DIR / "video.mp4", "video"
        elif ext in [".mp3", ".wav"]: target, mode = MEDIA_DIR / "audio.mp3", None
        elif ext in [".jpg", ".png"]: target, mode = MEDIA_DIR / "image.jpg", None
        else: target, mode = MEDIA_DIR / "video.mp4", "video"
        if target.exists(): target.unlink()
        o_path.rename(target)
        if mode: CONFIG["mode"] = mode; save_config(CONFIG)
        await m.edit_text("✅ **Successfully Updated Media!**", parse_mode="Markdown")
    except Exception as e: await m.edit_text(f"❌ Error: {e}")

async def mode_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args: return
    m = ctx.args[0].lower()
    if m in ["video", "radio", "overlay"]:
        CONFIG["mode"] = m; save_config(CONFIG)
        await update.message.reply_text(f"✅ Mode: `{m}`")

async def quality_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args: return
    q = ctx.args[0].lower()
    if q in ["1080p", "720p", "360p"]:
        CONFIG["quality"] = q; save_config(CONFIG)
        await update.message.reply_text(f"✅ Quality: `{q}`")

async def inline_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_live": await start_live_logic(query)
    elif query.data == "stop_live": await stop_live_logic(query)
    elif query.data == "status_check": await status_logic(query)
    elif query.data == "show_help": await query.message.reply_text("📖 Set Key -> Set Source -> Start Live!", parse_mode="Markdown")

# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
def main():
    logger.info("Bot starting in Universal Mode...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("quality", quality_cmd))
    app.add_handler(CommandHandler("source", source_cmd))
    app.add_handler(CallbackQueryHandler(inline_callback))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), state_and_upload_handler))
    app.run_polling()

if __name__ == "__main__": main()
