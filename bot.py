# ========================================================================
# LIVEXABOT: MULTI-SESSION DAEMON (V3.0)
# Version: 3.0 • Panel Integration • Socket IPC • 1080p
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
# PATHS & CONFIG
# ------------------------------------------------------------------------
BASE = Path("/home/container") if Path("/home/container").exists() else Path.cwd()
STORAGE = BASE / "storage"
STORAGE.mkdir(exist_ok=True)
MEDIA_DIR = STORAGE / "media"
MEDIA_DIR.mkdir(exist_ok=True)
SESSIONS_FILE = STORAGE / "sessions_v3.json"
SOCKET_PATH = "/tmp/livexa_stream.sock"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LivexaBot")

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "PASTE_YOUR_TOKEN_HERE"
ADMIN_ID = os.environ.get("ADMIN_ID")
SESSIONS = {}
USER_STATE = {}

# ------------------------------------------------------------------------
# PERSISTENCE
# ------------------------------------------------------------------------
def load_sessions():
    global SESSIONS
    if SESSIONS_FILE.exists():
        try:
            data = json.loads(SESSIONS_FILE.read_text())
            for sid, sdata in data.items():
                pid = sdata.get("pid")
                if pid and not psutil.pid_exists(pid): sdata["pid"] = None
            SESSIONS = data
        except: SESSIONS = {}

def save_sessions():
    try: SESSIONS_FILE.write_text(json.dumps(SESSIONS, indent=2))
    except: pass

# ------------------------------------------------------------------------
# IPC SERVER (UNIX SOCKET)
# ------------------------------------------------------------------------
async def handle_ipc(reader, writer):
    data = await reader.read(4096)
    if not data: return
    try:
        req = json.loads(data.decode().strip())
        action = req.get("action")
        res = {"status": "error", "message": "Unknown action"}

        if action == "status":
            res = {"status": "success", "active": sum(1 for s in SESSIONS.values() if s.get("pid")), "total": len(SESSIONS)}
        elif action == "list_sessions":
            res = {"status": "success", "sessions": SESSIONS}
        elif action == "start":
            sid = req.get("session_id")
            media = req.get("media_source")
            quality = req.get("quality", "720p")
            res = await start_session_logic(sid, media, quality)
        elif action == "stop":
            res = await stop_session_logic(req.get("session_id"))
        elif action == "system_info":
            res = {"status": "success", "cpu_percent": psutil.cpu_percent(), "memory_percent": psutil.virtual_memory().percent}

        writer.write(json.dumps(res).encode() + b'\n')
        await writer.drain()
    except Exception as e:
        logger.error(f"IPC Error: {e}")
    finally:
        writer.close()

async def start_ipc_server():
    if Path(SOCKET_PATH).exists(): os.unlink(SOCKET_PATH)
    server = await asyncio.start_unix_server(handle_ipc, SOCKET_PATH)
    logger.info(f"IPC Server started at {SOCKET_PATH}")
    async with server: await server.serve_forever()

# ------------------------------------------------------------------------
# STREAM LOGIC
# ------------------------------------------------------------------------
async def start_session_logic(sid, media, quality="720p"):
    if not sid or not media: return {"status": "error", "message": "Missing ID or Media"}
    if sid in SESSIONS and SESSIONS[sid].get("pid") and psutil.pid_exists(SESSIONS[sid]["pid"]):
        return {"status": "error", "message": "Session already running"}

    # For simplicity in this demo, we assume media is already local or handles gdown here
    # (Full implementation would include gdown download logic from previous versions)
    
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{SESSIONS.get(sid, {}).get('key', '')}"
    if not SESSIONS.get(sid, {}).get('key'): return {"status": "error", "message": "No key for this session"}

    # Minimal FFmpeg command for demo reliability
    cmd = ["ffmpeg", "-re", "-i", media, "-c:v", "libx264", "-preset", "veryfast", "-f", "flv", rtmp]
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        await asyncio.sleep(2)
        if proc.poll() is not None: return {"status": "error", "message": "FFmpeg failed"}
        
        SESSIONS[sid] = SESSIONS.get(sid, {"key": SESSIONS[sid]["key"]})
        SESSIONS[sid].update({"pid": proc.pid, "media": media, "quality": quality, "status": "active"})
        save_sessions()
        return {"status": "success", "message": f"Started {sid}"}
    except Exception as e: return {"status": "error", "message": str(e)}

async def stop_session_logic(sid):
    if sid not in SESSIONS or not SESSIONS[sid].get("pid"): return {"status": "error", "message": "Not running"}
    pid = SESSIONS[sid]["pid"]
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        SESSIONS[sid]["pid"] = None
        SESSIONS[sid]["status"] = "stopped"
        save_sessions()
        return {"status": "success", "message": f"Stopped {sid}"}
    except: return {"status": "error", "message": "Kill failed"}

# ------------------------------------------------------------------------
# TELEGRAM HANDLERS
# ------------------------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **LIVEXABOT V3.0 (MULTI-LIVE)**\nManage via Panel at `kumar9x.qzz.io` or use commands here.", parse_mode="Markdown")

async def setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or len(ctx.args) < 2: return await update.message.reply_text("Usage: `/setkey <id> <key>`", parse_mode="Markdown")
    sid, key = ctx.args[0], ctx.args[1]
    SESSIONS[sid] = SESSIONS.get(sid, {})
    SESSIONS[sid]["key"] = key
    save_sessions()
    await update.message.reply_text(f"✅ Key set for `{sid}`", parse_mode="Markdown")

# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
async def main():
    load_sessions()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setkey", setkey))
    
    # Run Telegram Bot and IPC Server concurrently
    await asyncio.gather(
        app.initialize(),
        app.start_polling(),
        start_ipc_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
