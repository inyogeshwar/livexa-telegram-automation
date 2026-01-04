# ===============================
# TELEGRAM IMAGE → YOUTUBE LIVE BOT (PREMIUM)
# HD 720p • Persistent Sessions • Robust
# ===============================

import os
import signal
import subprocess
import json
import asyncio
import logging
from pathlib import Path

import gdown
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------------------
# CONFIG
# -------------------------------
BOT_TOKEN = "7811290443:AAE4F53WPDCHcIZJodLTQooRXQx10TMtR28" 
PORT = 8080

BASE = Path("/opt/livexa")
STORAGE = BASE / "storage"
STORAGE.mkdir(exist_ok=True, parents=True) # Ensure storage exists

PID_FILE = STORAGE / "pids.json"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------------
# PERSISTENCE HELPERS
# -------------------------------
def load_pids() -> dict:
    """Load active process IDs from disk to recover sessions after restart."""
    if not PID_FILE.exists():
        return {}
    try:
        data = json.loads(PID_FILE.read_text())
        # Verify if processes are actually alive
        validated = {}
        for cid, pid in data.items():
            try:
                os.kill(pid, 0) # Check if process exists
                validated[cid] = pid
            except OSError:
                logger.info(f"Process {pid} for chat {cid} is dead, removing.")
        return validated
    except Exception as e:
        logger.error(f"Failed to load PIDs: {e}")
        return {}

def save_pids(active: dict):
    """Save active process IDs to disk."""
    try:
        PID_FILE.write_text(json.dumps(active))
    except Exception as e:
        logger.error(f"Failed to save PIDs: {e}")

# Global Active Processes (InMemory + Sync with Disk)
ACTIVE = load_pids()

def update_active(cid, pid=None):
    """Update global state and persist."""
    if pid:
        ACTIVE[str(cid)] = pid
    else:
        ACTIVE.pop(str(cid), None)
    save_pids(ACTIVE)

# -------------------------------
# CHAT HELPERS
# -------------------------------
def chat_dir(cid) -> Path:
    d = STORAGE / str(cid)
    d.mkdir(exist_ok=True)
    return d

def cfg_path(cid) -> Path:
    return chat_dir(cid) / "config.json"

def load_cfg(cid) -> dict:
    p = cfg_path(cid)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except:
            return {}
    return {}

def save_cfg(cid, data: dict):
    cfg_path(cid).write_text(json.dumps(data))

# -------------------------------
# COMMANDS
# -------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **HD Link Stream Bot (Premium)**\n\n"
        "1️⃣ **/set_stream** `<key>`\n"
        "2️⃣ **/set_audio** `<GDrive_Link>`\n"
        "3️⃣ Send an **Image**\n"
        "4️⃣ **/start_stream**\n"
        "5️⃣ **/stop_stream**\n"
        "6️⃣ **/status**\n\n"
        "✨ _Supports 720p HD, Auto-Reconnect, Persistent Sessions_"
    , parse_mode="Markdown")

async def set_stream(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.message.reply_text("❌ Usage: `/set_stream <key>`", parse_mode="Markdown")

    key = ctx.args[0].strip()
    save_cfg(update.effective_chat.id, {"key": key})
    await update.message.reply_text("✅ **Stream Key Saved!**", parse_mode="Markdown")

async def set_audio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.message.reply_text("❌ Usage: `/set_audio <GDrive_Link>`", parse_mode="Markdown")

    cid = update.effective_chat.id
    d = chat_dir(cid)
    out = d / "audio.mp3"
    
    msg = await update.message.reply_text("⏳ **Downloading from Google Drive...**", parse_mode="Markdown")

    try:
        if out.exists(): out.unlink()
        
        # Download in thread to not block bot
        await asyncio.to_thread(
            gdown.download,
            ctx.args[0],
            str(out),
            quiet=False,
            fuzzy=True
        )

        if out.exists() and out.stat().st_size > 50 * 1024: # Min 50KB
            await msg.edit_text("✅ **Audio Downloaded Successfully!** (Ready to stream)", parse_mode="Markdown")
        else:
            await msg.edit_text("❌ **Download Failed.** File too small or inaccessible.", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

async def upload_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    cid = msg.chat.id
    d = chat_dir(cid)

    # IMAGE HANDLER
    if msg.photo:
        f = await msg.photo[-1].get_file()
        await f.download_to_drive(d / "image.jpg")
        return await msg.reply_text("🖼️ **Background Image Set!**", parse_mode="Markdown")

    # AUDIO HANDLER (Telegram Upload)
    audio = msg.audio or msg.document
    if audio:
        fname = (audio.file_name or "").lower()
        if fname.endswith('.mp3') or audio.mime_type == 'audio/mpeg':
            f = await audio.get_file()
            await f.download_to_drive(d / "audio.mp3")
            await msg.reply_text("🎵 **MP3 File Uploaded!**", parse_mode="Markdown")
        else:
            if msg.document: # Only warn if it was a document upload attempt
                return # Silent ignore random files
            await msg.reply_text("⚠️ Please upload an **MP3** file.")

async def start_stream(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    str_cid = str(cid)

    # Check if already running
    if str_cid in ACTIVE:
        try:
            os.kill(ACTIVE[str_cid], 0)
            return await update.message.reply_text("⚠️ **Stream is already running!**", parse_mode="Markdown")
        except OSError:
            update_active(cid, None) # Cleanup dead PID

    # valid configuration
    cfg = load_cfg(cid)
    if "key" not in cfg:
        return await update.message.reply_text("❌ **No Stream Key!** use /set_stream", parse_mode="Markdown")

    d = chat_dir(cid)
    image = d / "image.jpg"
    audio = d / "audio.mp3"

    if not image.exists():
        return await update.message.reply_text("❌ **Missing Image!** Send a photo first.", parse_mode="Markdown")
    if not audio.exists():
        return await update.message.reply_text("❌ **Missing Audio!** Use /set_audio or send MP3.", parse_mode="Markdown")

    # Construct RTMP URL
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{cfg['key']}"

    # FFMPEG COMMAND (PREMIUM QUALITY)
    # 720p @ 2500k video, 192k audio
    cmd = [
        "ffmpeg",
        "-re",
        "-loop", "1", "-i", str(image),
        "-stream_loop", "-1", "-i", str(audio),
        "-vf", "scale=1280:720,format=yuv420p", # Fixed 720p scaling
        "-c:v", "libx264",
        "-preset", "veryfast", # Better quality than ultrafast
        "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", # Keyframe every 2s for 30fps
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-f", "flv",
        rtmp
    ]

    try:
        # Start Process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Immediate crash check
        await asyncio.sleep(2)
        if proc.poll() is not None:
             _, err = proc.communicate()
             error_msg = err.decode('utf-8')[-300:] if err else "Unknown Error"
             return await update.message.reply_text(f"❌ **Stream Failed to Start:**\n`{error_msg}`", parse_mode="Markdown")

        # Success - Identify PID and Save
        update_active(cid, proc.pid)
        await update.message.reply_text(f"✅ **Stream Started!** (PID: {proc.pid})\n📊 Quality: 720p HD @ 2.5Mbps", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ System Error: {e}")

async def stop_stream(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    str_cid = str(cid)
    
    pid = ACTIVE.get(str_cid)
    
    if not pid:
        return await update.message.reply_text("⚠️ No active stream found.", parse_mode="Markdown")

    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM) # Kill process group
        await update.message.reply_text("⏹ **Stream Stopped Successfully.**")
    except ProcessLookupError:
        await update.message.reply_text("⚠️ Stream process was already dead.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error stopping stream: {e}")
    
    update_active(cid, None)

async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    str_cid = str(cid)
    pid = ACTIVE.get(str_cid)
    
    is_running = False
    if pid:
        try:
            os.kill(pid, 0)
            is_running = True
        except OSError:
            update_active(cid, None) # Cleanup

    if is_running:
        await update.message.reply_text(
            f"🟢 **ONLINE**\n"
            f"🆔 PID: `{pid}`\n"
            f"📊 Quality: 720p HD",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🔴 **OFFLINE**", parse_mode="Markdown")

# -------------------------------
# MAIN
# -------------------------------
def main():
    print("🤖 Bot Starting... (Premium V2)")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_stream", set_stream))
    app.add_handler(CommandHandler("set_audio", set_audio))
    app.add_handler(CommandHandler("start_stream", start_stream))
    app.add_handler(CommandHandler("stop_stream", stop_stream))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.ALL, upload_handler))

    app.run_polling()

if __name__ == "__main__":
    main()

