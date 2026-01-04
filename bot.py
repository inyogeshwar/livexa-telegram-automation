# ========================================================================
# LIVEXABOT: PERSONAL MULTI-LIVE YOUTUBE STREAMING AUTOMATION
# Version: 1.2 (ULTRA) • GDrive Support • Video/Radio/Overlay • 1080p
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
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------------------------------------------------------------
# CONFIG & DIRECTORIES
# ------------------------------------------------------------------------
BOT_TOKEN = "7811290443:AAE4F53WPDCHcIZJodLTQooRXQx10TMtR28" 
BASE = Path("/opt/livexa")
STORAGE = BASE / "storage"
LIVES_DIR = STORAGE / "lives"
LIVES_DIR.mkdir(exist_ok=True, parents=True)

SESSIONS_FILE = STORAGE / "sessions.json"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("LivexaBot")

# Whitelist (Admin ID)
ADMIN_ID = None 

# ------------------------------------------------------------------------
# SESSION & SESSION TRACKING
# ------------------------------------------------------------------------
SESSIONS = {}

def load_sessions():
    """Load session state from disk and verify PIDs."""
    if not SESSIONS_FILE.exists(): return {}
    try:
        data = json.loads(SESSIONS_FILE.read_text())
        validated = {}
        for lid, info in data.items():
            pid = info.get("pid")
            if pid:
                if psutil.pid_exists(pid):
                    try:
                        p = psutil.Process(pid)
                        if "ffmpeg" in p.name().lower(): validated[lid] = info
                    except: pass
            else: validated[lid] = info
        return validated
    except: return {}

def save_sessions():
    """Commit global SESSIONS state to disk."""
    try: SESSIONS_FILE.write_text(json.dumps(SESSIONS, indent=2))
    except: pass

# Initial Load
SESSIONS = load_sessions()

# ------------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------------
def get_live_dir(lid: str) -> Path:
    d = LIVES_DIR / lid
    d.mkdir(exist_ok=True)
    return d

def update_config(lid: str, **kwargs):
    if lid not in SESSIONS:
        SESSIONS[lid] = {"quality": "720p", "source": "telegram", "mode": "video"}
    SESSIONS[lid].update(kwargs)
    save_sessions()

async def admin_only(update: Update):
    global ADMIN_ID
    uid = update.effective_user.id
    if ADMIN_ID is None: ADMIN_ID = uid
    return uid == ADMIN_ID

# ------------------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    await update.message.reply_text(
        "🚀 **LIVEXABOT ULTRA V1.2**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆕 `/newlive` - Create session\n"
        "🔑 `/setkey <id> <key>` - Set stream key\n"
        "🎬 `/mode <id> video|radio|overlay` - Set stream type\n"
        "📊 `/quality <id> 1080p|720p|360p` - Set resolution\n"
        "📂 `/source <id> <url>` - Download from GDrive\n"
        "🚀 `/start_live <id>` - **GO LIVE**\n"
        "⏹ `/stop <id>` - STOP LIVE\n"
        "📜 `/livelist` - Show sessions\n"
        "🆔 `/status <id>` - Session info\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **Source Tip:** GDrive links ko `/source` se download karein."
    , parse_mode="Markdown")

async def new_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    lid = f"live-{int(time.time() % 10000):04d}"
    update_config(lid, chat_id=update.effective_chat.id)
    await update.message.reply_text(f"✅ **Created Session:** `{lid}`", parse_mode="Markdown")

async def livelist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not SESSIONS: return await update.message.reply_text("📭 No sessions.")
    text = "📜 **Current Sessions:**\n\n"
    for lid, info in SESSIONS.items():
        status = "🟢 ONLINE" if info.get("pid") else "💤 IDLE"
        text += f"🔹 `{lid}`: {status} | Mode: `{info.get('mode')}` | Q: `{info.get('quality')}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/mode <id> video|radio|overlay`")
    lid, mode = ctx.args[0], ctx.args[1].lower()
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, mode=mode)
    await update.message.reply_text(f"✅ Mode for `{lid}` set to `{mode}`")

async def setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/setkey <id> <key>`")
    lid, key = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, key=key)
    await update.message.reply_text(f"✅ Key updated for `{lid}`")

async def quality(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/quality <id> resolution`")
    lid, q = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, quality=q)
    await update.message.reply_text(f"✅ Quality set to `{q}` for `{lid}`")

async def source_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2: return await update.message.reply_text("❌ `/source <id> <gdrive_url>`")
    lid, url = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Unknown ID.")
    
    msg = await update.message.reply_text(f"⏳ Downloading from GDrive for `{lid}`...")
    ldir = get_live_dir(lid)
    
    try:
        # Download to a temporary file first to determine extension
        temp_path = ldir / f"temp_{int(time.time())}"
        out = await asyncio.to_thread(gdown.download, url, str(temp_path), quiet=True, fuzzy=True)
        
        if not out or not Path(out).exists():
            return await msg.edit_text("❌ Download failed. Link check karein.")

        out_path = Path(out)
        ext = out_path.suffix.lower()
        
        final_file = None
        if ext in [".mp4", ".mkv", ".mov"]:
            final_file = ldir / "video.mp4"
            update_config(lid, mode="video")
            msg_txt = "📹 Video set!"
        elif ext in [".mp3", ".wav", ".m4a"]:
            final_file = ldir / "audio.mp3"
            msg_txt = "🎵 Audio set!"
        elif ext in [".jpg", ".jpeg", ".png"]:
            final_file = ldir / "image.jpg"
            msg_txt = "🖼 Image set!"
        else:
            # Fallback based on current mode or size
            if out_path.stat().st_size > 10 * 1024 * 1024:
                final_file = ldir / "video.mp4"
                msg_txt = "📹 Video set (guessed by size)!"
            else:
                final_file = ldir / "audio.mp3"
                msg_txt = "🎵 Audio set (guessed by size)!"

        if final_file:
            if final_file.exists(): final_file.unlink()
            out_path.rename(final_file)
            await msg.edit_text(f"✅ {msg_txt} for `{lid}`")
        else:
            out_path.unlink()
            await msg.edit_text("❌ Unsupported file type.")
            
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def start_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ `/start_live <id>`")
    lid = ctx.args[0]
    info = SESSIONS.get(lid)
    if not info: return await update.message.reply_text("❌ Invalid ID.")
    if info.get("pid"): return await update.message.reply_text("⚠️ Already running.")
    if not info.get("key"): return await update.message.reply_text("❌ Set stream key first.")

    ldir = get_live_dir(lid)
    img, aud, vid = ldir / "image.jpg", ldir / "audio.mp3", ldir / "video.mp4"
    mode = info.get("mode", "video")

    if mode == "video" and not vid.exists():
        return await update.message.reply_text(f"❌ Video (`video.mp4`) missing in `{lid}`.")
    if mode == "radio" and (not img.exists() or not aud.exists()):
        return await update.message.reply_text(f"❌ Radio requires Image + Audio in `{lid}`.")
    if mode == "overlay" and (not vid.exists() or not aud.exists()):
        return await update.message.reply_text(f"❌ Overlay requires Video + Audio in `{lid}`.")

    q_map = {"360p": ("640:360", "800k", "128k"), "720p": ("1280:720", "2500k", "192k"), "1080p": ("1920:1080", "4500k", "256k")}
    res, b_v, b_a = q_map.get(info.get("quality", "720p"), q_map["720p"])
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{info['key']}"

    cmd = ["ffmpeg", "-re"]
    if mode == "video": cmd += ["-stream_loop", "-1", "-i", str(vid)]
    elif mode == "radio": cmd += ["-loop", "1", "-i", str(img), "-stream_loop", "-1", "-i", str(aud)]
    elif mode == "overlay": cmd += ["-stream_loop", "-1", "-i", str(vid), "-stream_loop", "-1", "-i", str(aud), "-map", "0:v", "-map", "1:a", "-shortest"]

    cmd += ["-vf", f"scale={res},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-b:v", b_v, "-maxrate", b_v, "-bufsize", "5000k", "-g", "60", "-c:a", "aac", "-b:a", b_a, "-ar", "44100", "-f", "flv", rtmp]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        await asyncio.sleep(3)
        if proc.poll() is not None:
            _, err = proc.communicate()
            return await update.message.reply_text(f"❌ Start Failed for `{lid}`:\n`{err.decode()[-200:]}`")
        update_config(lid, pid=proc.pid)
        await update.message.reply_text(f"🚀 **LIVE STARTED!**\n🆔 `{lid}` | Mode: `{mode}`\n📊 `{res}` HD", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ System Error: {e}")

async def stop_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ `/stop <id>`")
    lid = ctx.args[0]
    pid = SESSIONS.get(lid, {}).get("pid")
    if not pid: return await update.message.reply_text("⚠️ Not running.")
    try: os.killpg(os.getpgid(pid), signal.SIGTERM)
    except: pass
    update_config(lid, pid=None)
    await update.message.reply_text(f"⏹ **Stopped `{lid}`**")

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ `/status <id>`")
    lid = ctx.args[0]
    info = SESSIONS.get(lid)
    if not info: return await update.message.reply_text("❌ Unknown ID.")
    alive = False
    if info.get("pid"):
        try:
            os.kill(info["pid"], 0)
            alive = True
        except: update_config(lid, pid=None)
    await update.message.reply_text(f"📊 `{lid}` Status:\nState: {'🟢 ON' if alive else '💤 OFF'}\nMode: `{info.get('mode')}`\nQ: `{info.get('quality')}`", parse_mode="Markdown")

async def upload_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    msg = update.message
    if not SESSIONS: return await msg.reply_text("❌ Create session first.")
    lid = sorted(SESSIONS.keys())[-1]
    ldir = get_live_dir(lid)
    
    if msg.photo:
        f = await msg.photo[-1].get_file()
        await f.download_to_drive(ldir / "image.jpg")
        return await msg.reply_text(f"🖼 Image set for `{lid}`")

    media = msg.video or msg.audio or msg.document
    if not media: return
    fname = (media.file_name or "").lower()
    
    if msg.video or fname.endswith(".mp4"):
        f = await media.get_file()
        await f.download_to_drive(ldir / "video.mp4")
        if SESSIONS[lid].get("mode") == "radio": update_config(lid, mode="video")
        return await msg.reply_text(f"📹 Video set for `{lid}`")
        
    if msg.audio or fname.endswith(".mp3"):
        f = await media.get_file()
        await f.download_to_drive(ldir / "audio.mp3")
        return await msg.reply_text(f"🎵 Audio set for `{lid}`")

def main():
    print("🤖 LivexaBot ULTRA V1.2 Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newlive", new_live))
    app.add_handler(CommandHandler("livelist", livelist))
    app.add_handler(CommandHandler("setkey", setkey))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("quality", quality))
    app.add_handler(CommandHandler("source", source_cmd))
    app.add_handler(CommandHandler("start_live", start_live))
    app.add_handler(CommandHandler("stop", stop_live))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.ALL, upload_agent))
    app.run_polling()

if __name__ == "__main__": main()

