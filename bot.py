# ========================================================================
# LIVEXABOT: PERSONAL MULTI-LIVE YOUTUBE STREAMING AUTOMATION
# Version: 1.0 (PRO) • Multi-Session • Resource-Aware • Stable
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

# Whitelist (Admin ID) - Can be injected by installer or set on first start
ADMIN_ID = None 

# ------------------------------------------------------------------------
# SESSION & SESSION TRACKING
# ------------------------------------------------------------------------
# Memory state: { "live_1": { "pid": 123, "quality": "720p", "key": "...", "chat_id": ... } }
SESSIONS = {}

def load_sessions():
    """Load session state from disk and verify PIDs."""
    global SESSIONS
    if not SESSIONS_FILE.exists():
        return {}
    try:
        data = json.loads(SESSIONS_FILE.read_text())
        validated = {}
        for lid, info in data.items():
            pid = info.get("pid")
            if pid:
                try:
                    p = psutil.Process(pid)
                    if p.is_running() and "ffmpeg" in p.name().lower():
                        validated[lid] = info
                    else:
                        logger.info(f"Removing dead session {lid} (PID {pid} not ffmpeg)")
                except:
                    logger.info(f"Removing dead session {lid} (PID {pid} not found)")
            else:
                validated[lid] = info # Key/Config but not running
        return validated
    except Exception as e:
        logger.error(f"Failed to load sessions: {e}")
        return {}

def save_sessions():
    """Commit global SESSIONS state to disk."""
    try:
        SESSIONS_FILE.write_text(json.dumps(SESSIONS, indent=2))
    except Exception as e:
        logger.error(f"Failed to save sessions: {e}")

# Initial Load
SESSIONS = load_sessions()

# ------------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------------
def get_live_dir(lid: str) -> Path:
    d = LIVES_DIR / lid
    d.mkdir(exist_ok=True)
    return d

def get_config(lid: str) -> dict:
    return SESSIONS.get(lid, {})

def update_config(lid: str, **kwargs):
    if lid not in SESSIONS:
        SESSIONS[lid] = {"quality": "720p", "source": "telegram"}
    SESSIONS[lid].update(kwargs)
    save_sessions()

async def admin_only(update: Update):
    global ADMIN_ID
    uid = update.effective_user.id
    if ADMIN_ID is None: # First user becomes admin
        ADMIN_ID = uid
        return True
    return uid == ADMIN_ID

# ------------------------------------------------------------------------
# RESOURCE MONITOR & AUTO-QUALITY
# ------------------------------------------------------------------------
async def resource_monitor():
    """Background loop to check server pressure and log status."""
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        active_count = sum(1 for s in SESSIONS.values() if s.get("pid"))
        
        if cpu > 85 or ram > 90:
            logger.warning(f"CRITICAL RESOURCE PRESSURE: CPU {cpu}% | RAM {ram}%")
            # Logic for Auto-Quality degradation could go here
            # e.g., finding the highest quality stream and asking it to restart at lower q
            
        await asyncio.sleep(60)

# ------------------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎬 **LIVEXABOT MASTER**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆕 `/newlive` - Create a new session\n"
        "🔑 `/setkey <id> <key>` - Set stream key\n"
        "📂 `/source <id> telegram|gdrive` - Set source type\n"
        "📊 `/quality <id> auto|360p|720p|1080p` - Set quality\n"
        "🚀 `/start_live <id>` - Start streaming\n"
        "⏹ `/stop <id>` - Stop streaming\n"
        "🆔 `/status <id>` - Session status\n"
        "📜 `/livelist` - List all sessions\n"
        "❌ `/kill <id>` - Delete session data\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    , parse_mode="Markdown")

async def new_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    lid = f"live-{int(time.time() % 10000):04d}"
    update_config(lid, chat_id=update.effective_chat.id)
    await update.message.reply_text(f"✅ **Created Session:** `{lid}`", parse_mode="Markdown")

async def livelist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not SESSIONS:
        return await update.message.reply_text("📭 No active sessions.")
    
    text = "📜 **Active Sessions:**\n\n"
    for lid, info in SESSIONS.items():
        status = "🟢 ONLINE" if info.get("pid") else "💤 IDLE"
        text += f"🔹 `{lid}`: {status} | Q: `{info.get('quality')}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2:
        return await update.message.reply_text("❌ Usage: `/setkey <id> <stream_key>`", parse_mode="Markdown")
    lid, key = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, key=key)
    await update.message.reply_text(f"✅ Key updated for `{lid}`", parse_mode="Markdown")

async def quality(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2:
        return await update.message.reply_text("❌ Usage: `/quality <id> auto|360p|720p|1080p`", parse_mode="Markdown")
    lid, q = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    if q not in ["auto", "360p", "720p", "1080p"]:
        return await update.message.reply_text("❌ Invalid quality level.")
    update_config(lid, quality=q)
    await update.message.reply_text(f"✅ Quality set to `{q}` for `{lid}`", parse_mode="Markdown")

async def source_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if len(ctx.args) < 2:
        return await update.message.reply_text("❌ Usage: `/source <id> telegram|gdrive`", parse_mode="Markdown")
    lid, src = ctx.args[0], ctx.args[1]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    update_config(lid, source=src)
    await update.message.reply_text(f"✅ Source set to `{src}` for `{lid}`", parse_mode="Markdown")

async def start_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/start_live <id>`")
    lid = ctx.args[0]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Invalid ID.")
    
    info = SESSIONS[lid]
    if info.get("pid"):
        return await update.message.reply_text("⚠️ Already running.")

    if not info.get("key"):
        return await update.message.reply_text("❌ Missing Stream Key. Use /setkey")

    ldir = get_live_dir(lid)
    img, aud = ldir / "image.jpg", ldir / "audio.mp3"
    
    if not img.exists() or not aud.exists():
        return await update.message.reply_text(f"❌ Missing media in `{lid}`. Upload image/audio first.")

    # Quality Ladder
    q_map = {
        "360p":  ("640:360", "800k", "128k"),
        "720p":  ("1280:720", "2500k", "192k"),
        "1080p": ("1920:1080", "4500k", "256k"),
        "auto":  ("1280:720", "2500k", "192k") # Default to 720p
    }
    res, b_v, b_a = q_map.get(info.get("quality"), q_map["720p"])

    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{info['key']}"

    cmd = [
        "ffmpeg", "-re", "-loop", "1", "-i", str(img),
        "-stream_loop", "-1", "-i", str(aud),
        "-vf", f"scale={res},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", b_v, "-maxrate", b_v, "-bufsize", "5000k",
        "-g", "60", "-c:a", "aac", "-b:a", b_a, "-ar", "44100", "-f", "flv", rtmp
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        await asyncio.sleep(2)
        if proc.poll() is not None:
            _, err = proc.communicate()
            return await update.message.reply_text(f"❌ Start Failed for `{lid}`:\n`{err.decode()[-200:]}`")

        update_config(lid, pid=proc.pid)
        await update.message.reply_text(f"🚀 **Started `{lid}`**\n📊 Quality: `{res}` @ `{b_v}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ System Error: {e}")

async def stop_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/stop <id>`")
    lid = ctx.args[0]
    pid = SESSIONS.get(lid, {}).get("pid")
    
    if not pid: return await update.message.reply_text("⚠️ Not running.")
    
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        await update.message.reply_text(f"⏹ **Stopped `{lid}`**")
    except:
        await update.message.reply_text("⚠️ Process already dead.")
    
    update_config(lid, pid=None)

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/status <id>`")
    lid = ctx.args[0]
    info = SESSIONS.get(lid)
    if not info: return await update.message.reply_text("❌ Unknown ID.")
    
    alive = False
    if info.get("pid"):
        try:
            os.kill(info["pid"], 0)
            alive = True
        except:
            update_config(lid, pid=None)
            
    await update.message.reply_text(
        f"📊 **Status: {lid}**\n"
        f"State: {'🟢 ONLINE' if alive else '💤 IDLE'}\n"
        f"Quality: `{info.get('quality')}`\n"
        f"Source: `{info.get('source')}`\n"
        f"PID: `{info.get('pid', 'N/A')}`"
    , parse_mode="Markdown")

async def kill_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update): return
    if not ctx.args: return await update.message.reply_text("❌ Usage: `/kill <id>`")
    lid = ctx.args[0]
    if lid not in SESSIONS: return await update.message.reply_text("❌ Unknown ID.")
    
    # Stop if running
    pid = SESSIONS[lid].get("pid")
    if pid:
        try: os.killpg(os.getpgid(pid), signal.SIGTERM)
        except: pass
        
    SESSIONS.pop(lid)
    save_sessions()
    await update.message.reply_text(f"🗑 **Session `{lid}` deleted.**")

async def upload_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Router for all media uploads. Tries to find most recent 'active' session lid."""
    if not await admin_only(update): return
    msg = update.message
    
    # Strategy: Find any session created/modified in the last 10 mins, or ask for ID.
    # For now, we'll look for any "last_used_lid" or just use the only one if exists.
    if not SESSIONS:
        return await msg.reply_text("❌ Create a session first with /newlive")
    
    # Defaulting to most recent lid if none specified in context
    lid = sorted(SESSIONS.keys())[-1] 
    ldir = get_live_dir(lid)
    
    if msg.photo:
        f = await msg.photo[-1].get_file()
        await f.download_to_drive(ldir / "image.jpg")
        return await msg.reply_text(f"🖼 **Image set for `{lid}`**", parse_mode="Markdown")

    aud = msg.audio or msg.document
    if aud:
        fname = (aud.file_name or "").lower()
        if fname.endswith(".mp3"):
            f = await aud.get_file()
            await f.download_to_drive(ldir / "audio.mp3")
            return await msg.reply_text(f"🎵 **Audio set for `{lid}`**", parse_mode="Markdown")

# ------------------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------------------
def main():
    print("🤖 LivexaBot: Multi-Live V1.0 Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newlive", new_live))
    app.add_handler(CommandHandler("livelist", livelist))
    app.add_handler(CommandHandler("setkey", setkey))
    app.add_handler(CommandHandler("quality", quality))
    app.add_handler(CommandHandler("source", source_cmd))
    app.add_handler(CommandHandler("start_live", start_live))
    app.add_handler(CommandHandler("stop", stop_live))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(MessageHandler(filters.ALL, upload_agent))

    # Background tasks
    loop = asyncio.get_event_loop()
    loop.create_task(resource_monitor())

    app.run_polling()

if __name__ == "__main__":
    main()

