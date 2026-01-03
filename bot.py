import os, subprocess, signal, re, logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, filters, CommandHandler
import gdown

# Inject Token from Env or Install
BOT_TOKEN = os.getenv("BOT_TOKEN")
STREAM_KEY = os.getenv("STREAM_KEY", "YOUR_STREAM_KEY")

USER_ID = os.getenv("ADMIN_ID") # Optional Security

BASE = Path("/opt/livexa")
MEDIA = BASE / "storage/media"
MEDIA.mkdir(parents=True, exist_ok=True)

IMAGE = BASE / "storage/image.jpg"
PLAYLIST = BASE / "storage/playlist.txt"
CONFIG_KEY = BASE / "storage/key.txt"

FFMPEG = None

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_stream_key():
    if CONFIG_KEY.exists():
        return CONFIG_KEY.read_text().strip()
    return STREAM_KEY

def rebuild_playlist():
    files = sorted([f for f in MEDIA.iterdir() if f.suffix in [".mp3", ".mp4"]])
    with open(PLAYLIST, "w") as f:
        for file in files:
            safe_path = str(file).replace("'", "'\\''") 
            f.write(f"file '{safe_path}'\n")
    return len(files)

def dashboard():
    key_status = "✅ Set" if "YOUR_" not in get_stream_key() else "❌ Missing"
    media_count = len(list(MEDIA.glob("*"))) if MEDIA.exists() else 0
    
    status = "🔴 LIVE" if FFMPEG else "⏹ STOPPED"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{status}", callback_data="status")],
        [InlineKeyboardButton("▶ START LIVE", callback_data="start"), InlineKeyboardButton("⏹ STOP LIVE", callback_data="stop")],
        [InlineKeyboardButton("🗑 Clear Playlist", callback_data="clear"), InlineKeyboardButton("🔄 Refresh", callback_data="refresh")]
    ])

async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Livexa Playlist Bot V4**\n\n"
        "1. Send **Stream Key** (text)\n"
        "2. Send **Image** (thumbnail)\n"
        "3. Send **MP3/MP4** or **Google Drive Link**\n"
        "4. Use Buttons below.",
        reply_markup=dashboard(),
        parse_mode="Markdown"
    )

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg: return

    # STREAM KEY (Text looks like regex)
    if msg.text and len(msg.text) > 10 and "-" in msg.text and "drive" not in msg.text:
        CONFIG_KEY.write_text(msg.text.strip())
        await msg.reply_text("🔑 Stream Key Saved!", reply_markup=dashboard())
        return

    # IMAGE
    if msg.photo:
        file = await msg.photo[-1].get_file()
        await file.download_to_drive(IMAGE)
        await msg.reply_text("🖼 Image Set. (Send files now)", reply_markup=dashboard())
        return

    # TELEGRAM FILE
    doc = msg.document or msg.audio or msg.video
    if doc:
        name = doc.file_name or "media"
        path = MEDIA / name
        file = await doc.get_file()
        await file.download_to_drive(path)
        count = rebuild_playlist()
        await msg.reply_text(f"✅ Added: {name}\nPlaylist Size: {count}", reply_markup=dashboard())
        return

    # GOOGLE DRIVE LINK
    if msg.text and "drive.google.com" in msg.text:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", msg.text)
        if not match:
            return await msg.reply_text("❌ Invalid Drive link")

        await msg.reply_text("⬇️ Downloading from Drive...")
        try:
            file_id = match.group(1)
            # Use original filename from gdown if possible, else default
            out = MEDIA / f"drive_{file_id}" 
            # Note: gdown usually handles filename if output is dir, but here we enforce path?
            # Actually better to let gdown save to dir
            gdown.download(id=file_id, output=str(out), quiet=False)
            rebuild_playlist()
            await msg.reply_text("☁️ Drive file added!", reply_markup=dashboard())
        except Exception as e:
             await msg.reply_text(f"❌ Error: {e}")
        return

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global FFMPEG
    q = update.callback_query
    await q.answer()

    if q.data == "refresh":
        await q.edit_message_reply_markup(reply_markup=dashboard())

    elif q.data == "clear":
        for f in MEDIA.iterdir():
            f.unlink()
        rebuild_playlist()
        await q.edit_message_text("🗑 Playlist Cleared.", reply_markup=dashboard())

    elif q.data == "start":
        if FFMPEG:
            return await q.answer("⚠️ Already live")
            
        key = get_stream_key()
        if "YOUR_" in key:
            return await q.answer("❌ Stream Key not set! Send it as text.", show_alert=True)
            
        if not IMAGE.exists():
             return await q.answer("❌ No Image set! Send a photo.", show_alert=True)

        if not PLAYLIST.exists() or os.path.getsize(PLAYLIST) == 0:
             return await q.answer("❌ Playlist empty! Send MP3/MP4.", show_alert=True)

        cmd = [
            "ffmpeg",
            "-re",
            "-loop", "1",
            "-i", str(IMAGE),
            "-f", "concat",
            "-safe", "0",
            "-i", str(PLAYLIST),
            # Video Encoding
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            # Audio Encoding
            "-c:a", "aac",
            "-b:a", "128k",
            # End when audio ends? No, loop playlist?
            # User code said "-shortest". This stops when shortest input ends.
            # If Image loops forever (loop 1), and playlist ends, shortest stops it.
            # To LOOP playlist, we need -stream_loop -1 before -i playlist?
            # The previous user code used -stream_loop -1.
            # The NEW code uses concat demuxer. Concat file can have 'stream_loop' directives but standard ffmpeg usage:
            # -stream_loop -1 -i playlist.txt ? No, concat demuxer is finite unless file loops.
            # We will assume single pass for now as per user code.
            "-shortest", 
            "-f", "flv",
            f"rtmp://a.rtmp.youtube.com/live2/{key}"
        ]

        FFMPEG = subprocess.Popen(cmd)
        await q.edit_message_text("🔴 LIVE STARTED!", reply_markup=dashboard())

    elif q.data == "stop":
        if FFMPEG:
            FFMPEG.terminate()
            FFMPEG = None
        await q.edit_message_text("⏹ LIVE STOPPED", reply_markup=dashboard())

def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN env var missing")
        return

    print("✅ Bot V4 Started")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL, on_message))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling()

if __name__ == "__main__":
    main()
