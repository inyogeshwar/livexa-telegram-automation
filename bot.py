# ========================================================================
# LIVEXABOT: PERSONAL MULTI-LIVE YOUTUBE STREAMING AUTOMATION
# Version: 1.4 (ULTRA) • Inline Menu • Button UI • GDrive Support
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
LIVES_DIR = STORAGE / "lives"
LIVES_DIR.mkdir(exist_ok=True, parents=True)
SESSIONS_FILE = STORAGE / "sessions.json"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("LivexaBot")

ADMIN_ID = None 

# ------------------------------------------------------------------------
# SESSION TRACKING
# ------------------------------------------------------------------------
SESSIONS = {}

def load_sessions():
    if not SESSIONS_FILE.exists(): return {}
    try:
        data = json.loads(SESSIONS_FILE.read_text())
        validated = {}
        for lid, info in data.items():
            pid = info.get("pid")
            if pid and psutil.pid_exists(pid):
                try:
                    p = psutil.Process(pid)
                    if "ffmpeg" in p.name().lower(): validated[lid] = info
                except: pass
            else: validated[lid] = info
        return validated
    except: return {}

def save_sessions():
    try: SESSIONS_FILE.write_text(json.dumps(SESSIONS, indent=2))
    except: pass

SESSIONS = load_sessions()

# ------------------------------------------------------------------------
# UI UTILS
# ------------------------------------------------------------------------
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🆕 New Live"), KeyboardButton("📜 Live List")],
        [KeyboardButton("🚀 Start Live"), KeyboardButton("⏹ Stop Live")],
        [KeyboardButton("📊 Status"), KeyboardButton("🎬 Change Mode")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_inline_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Create Session", callback_data="new_session")],
        [InlineKeyboardButton("📋 View All Lives", callback_data="list_sessions")],
        [InlineKeyboardButton("🛠 Setup Guide", callback_data="help_info")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_live_dir(lid: str) -> Path:
    d = LIVES_DIR / lid
    d.mkdir(exist_ok=True)
    return d

def update_config(lid: str, **kwargs):
    if lid not in SESSIONS:
        SESSIONS[lid] = {"quality": "720p", "mode": "video", "key": None}
    SESSIONS[lid].update(kwargs)
    save_sessions()

async def admin_only(update: Update):
    global ADMIN_ID
    uid = update.effective_user.id
    if ADMIN_ID is None: ADMIN_ID = uid
    return uid == ADMIN_ID

# ------------------------------------------------------------------------
# COMMAND & INLINE HANDLERS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    await update.message.reply_text(
        "🎬 **LIVEXABOT MASTER PANEL**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome! Use the interactive menu or buttons below.",
        parse_mode="Markdown",
        reply_markup=get_inline_menu()
    )
    await update.message.reply_text("Bottom dashboard active ✅", reply_markup=get_main_keyboard())

async def inline_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "new_session":
        lid = f"live-{int(time.time() % 10000):04d}"
        update_config(lid)
        await query.edit_message_text(f"✅ **Session Created:** `{lid}`\nSend media files (Img/Vid/Audio) to set up.", parse_mode="Markdown", reply_markup=get_inline_menu())
    
    elif query.data == "list_sessions":
        if not SESSIONS: return await query.edit_message_text("📭 No active sessions.", reply_markup=get_inline_menu())
        res = "📜 **Current Sessions:**\n\n"
        for lid, info in SESSIONS.items():
            status = "🟢 ON" if info.get("pid") else "💤 OFF"
            res += f"🔹 `{lid}`: {status} | Mode: `{info.get('mode')}`\n"
        await query.edit_message_text(res, parse_mode="Markdown", reply_markup=get_inline_menu())
        
    elif query.data == "help_info":
        await query.edit_message_text(
            "📖 **Quick Start:**\n"
            "1. Create session (button/command)\n"
            "2. Send/Source media files\n"
            "3. Set key: `/setkey <id> <key>`\n"
            "4. Start: `/start_live <id>`",
            parse_mode="Markdown", reply_markup=get_inline_menu()
        )

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    text = update.message.text
    if text == "🆕 New Live": return await new_live(update, ctx)
    if text == "📜 Live List": return await livelist(update, ctx)
    if text == "🚀 Start Live": return await update.message.reply_text("👉 Type: `/start_live <id>`")
    if text == "⏹ Stop Live": return await update.message.reply_text("👉 Type: `/stop <id>`")
    if text == "📊 Status": return await update.message.reply_text("👉 Type: `/status <id>`")
    if text == "🎬 Change Mode": return await update.message.reply_text("👉 Type: `/mode <id> video|radio|overlay`")

# ------------------------------------------------------------------------
# CORE LOGIC HANDLERS
# ------------------------------------------------------------------------
async def new_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lid = f"live-{int(time.time() % 10000):04d}"
    update_config(lid)
    await update.message.reply_text(f"✅ **Created Session:** `{lid}`", parse_mode="Markdown")

async def livelist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not SESSIONS: return await update.message.reply_text("📭 No sessions.")
    res = "📜 **Sessions:**\n\n"
    for lid, info in SESSIONS.items():
        status = "🟢 ONLINE" if info.get("pid") else "💤 IDLE"
        res += f"🔹 `{lid}`: {status} | Mode: `{info.get('mode')}` | Q: `{info.get('quality')}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

async def setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ Usage: `/setkey <id> <key>`")
    lid, key = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, key=key)
    await update.message.reply_text(f"✅ Key updated for `{lid}`")

async def quality(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ Usage: `/quality <id> resolution`")
    lid, q = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, quality=q)
    await update.message.reply_text(f"✅ Quality set to `{q}` for `{lid}`")

async def set_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/mode <id> video|radio|overlay`")
    lid, mode = ctx.args[0], ctx.args[1].lower()
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, mode=mode)
    await update.message.reply_text(f"✅ Mode for `{lid}` set to `{mode}`")

async def source_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/source <id> <url>`")
    lid, url = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Unknown ID.")
    
    msg = await update.message.reply_text(f"⏳ Downloading for `{lid}`...")
    ldir = get_live_dir(lid)
    try:
        temp = ldir / f"dl_{int(time.time())}"
        out = await asyncio.to_thread(gdown.download, url, str(temp), quiet=True, fuzzy=True)
        if not out: return await msg.edit_text("❌ Download failed.")
        o_path = Path(out)
        ext = o_path.suffix.lower()
        if ext in [".mp4", ".mkv", ".mov"]:
            target, mode, txt = ldir / "video.mp4", "video", "📹 Video set!"
        elif ext in [".mp3", ".wav", ".m4a"]:
            target, mode, txt = ldir / "audio.mp3", None, "🎵 Audio set!"
        elif ext in [".jpg", ".jpeg", ".png"]:
            target, mode, txt = ldir / "image.jpg", None, "🖼 Image set!"
        else:
            is_vid = o_path.stat().st_size > 5*1024*1024
            target, mode, txt = (ldir / "video.mp4", "video", "� Video set!") if is_vid else (ldir / "audio.mp3", None, "🎵 Audio set!")
            
        if target.exists(): target.unlink()
        o_path.rename(target)
        if mode: update_config(lid, mode=mode)
        await msg.edit_text(f"✅ {txt} for `{lid}`")
    except Exception as e: await msg.edit_text(f"❌ Error: {e}")

async def start_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/start_live <id>`")
    lid = ctx.args[0]
    info = SESSIONS.get(lid)
    if not info: return await update.message.reply_text("❌ Invalid ID.")
    if info.get("pid"): return await update.message.reply_text("⚠️ Already running.")
    if not info.get("key"): return await update.message.reply_text("❌ Missing Stream Key.")

    ldir = get_live_dir(lid)
    img, aud, vid = ldir / "image.jpg", ldir / "audio.mp3", ldir / "video.mp4"
    mode = info.get("mode")

    if mode == "video" and not vid.exists(): return await update.message.reply_text("❌ Video file missing.")
    if mode == "radio" and (not img.exists() or not aud.exists()):
        if vid.exists(): return await update.message.reply_text(f"❌ Radio requires Image+Audio. You have a Video file. Try: `/mode {lid} video`")
        return await update.message.reply_text("❌ Missing media for Radio.")
    if mode == "overlay" and (not vid.exists() or not aud.exists()): return await update.message.reply_text("❌ Missing media for Overlay.")

    q_map = {"360p": ("640:360","800k","128k"), "720p": ("1280:720","2500k","192k"), "1080p": ("1920:1080","4500k","256k")}
    res, bv, ba = q_map.get(info.get("quality"), q_map["720p"])
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{info['key']}"

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
        update_config(lid, pid=proc.pid)
        await update.message.reply_text(f"🚀 **LIVE STARTED!**\n🆔 `{lid}` | Mode: `{mode}`\n📊 `{res}` HD", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")

async def stop_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ `/stop <id>`")
    lid = ctx.args[0]
    pid = SESSIONS.get(lid, {}).get("pid")
    if not pid: return await update.message.reply_text("💤 Not running.")
    try: os.killpg(os.getpgid(pid), signal.SIGTERM)
    except: pass
    update_config(lid, pid=None)
    await update.message.reply_text(f"⏹ Stopped `{lid}`")

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/status <id>`")
    lid = ctx.args[0]
    info = SESSIONS.get(lid)
    if not info: return await update.message.reply_text("❌ Unknown ID.")
    alive = info.get("pid") and psutil.pid_exists(info["pid"])
    await update.message.reply_text(f"📊 `{lid}` Status:\nState: {'🟢 ON' if alive else '💤 OFF'}\nMode: `{info.get('mode')}`\nQ: `{info.get('quality')}`", parse_mode="Markdown")

async def upload_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    msg = update.message
    if not SESSIONS: return await msg.reply_text("❌ Create a session first.")
    lid = sorted(SESSIONS.keys())[-1]
    ldir = get_live_dir(lid)
    
    if msg.photo:
        await (await msg.photo[-1].get_file()).download_to_drive(ldir / "image.jpg")
        return await msg.reply_text(f"🖼 Image set for `{lid}`")
    media = msg.video or msg.audio or msg.document
    if not media: return
    fname = (media.file_name or "").lower()
    if msg.video or fname.endswith(".mp4"):
        await (await media.get_file()).download_to_drive(ldir / "video.mp4")
        if SESSIONS[lid].get("mode") == "radio": update_config(lid, mode="video")
        return await msg.reply_text(f"📹 Video set for `{lid}`")
    if msg.audio or fname.endswith(".mp3"):
        await (await media.get_file()).download_to_drive(ldir / "audio.mp3")
        return await msg.reply_text(f"🎵 Audio set for `{lid}`")

def main():
    print("🤖 LivexaBot ULTRA V1.4 Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newlive", new_live))
    app.add_handler(CommandHandler("livelist", livelist))
    app.add_handler(CommandHandler("setkey", setkey))
    app.add_handler(CommandHandler("quality", quality))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("source", source_cmd))
    app.add_handler(CommandHandler("start_live", start_live))
    app.add_handler(CommandHandler("stop", stop_live))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CallbackQueryHandler(inline_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), button_handler))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), upload_agent))
    app.run_polling()

if __name__ == "__main__": main()
