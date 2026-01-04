# README: LivexaBot PRO 🚀

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ━━━━━━━━━━ **L I V E X A B O T** ━━━━━━━━━━
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### **Personal Multi-Live YouTube Streaming Automation System**

**LivexaBot** is a high-reliability, Telegram-controlled automation system designed for personal creators who require multiple concurrent YouTube Live streams from a single powerful server.

---

## 🌟 Key Features
- **Multi-Live Streaming**: Run multiple independent live streams (different keys/media) simultaneously.
- **Auto-Quality Engine**: Monitors system resources (CPU/RAM) and manages quality levels (1080p, 720p, 360p).
- **Zero UI / Zero Code**: Control everything via Telegram commands.
- **PID Persistence**: Streams stay running and controllable even if the bot or server restarts.
- **HD Quality**: Optimized FFmpeg profiles for 720p and 1080p high-bitrate streaming.
- **Google Drive Integration**: Stream directly from Drive links.

---

## 🛠 One-Click Setup (CentOS / Ubuntu)

To install or update the system:
```bash
wget https://raw.githubusercontent.com/inyogeshwar/livexa-telegram-automation/main/install.sh
chmod +x install.sh
sudo ./install.sh "YOUR_TELEGRAM_BOT_TOKEN"
```

---

## 🤖 Telegram Commands

| Command | Action |
| --- | --- |
| `/newlive` | Create a new independent live session |
| `/setkey <id> <key>` | Assign YouTube stream key to a session |
| `/quality <id> <q>` | Set quality (360p, 720p, 1080p, auto) |
| `/start_live <id>` | Start the specific encoder instance |
| `/stop <id>` | Stop the specific live session |
| `/livelist` | View all sessions and their status |
| `/status <id>` | Detailed resource/state for a session |

---

## 🔐 Security
- **Admin Lock**: The first user to message the bot becomes the exclusive Administrator.
- **Resource Limits**: Automatically prevents server overload.

---

## 👤 Credits
**Owner**: [Yogeshwar Kumar](https://github.com/inyogeshwar)
**System**: LivexaBot PRO V1.0 - "Final · Locked · Complete"
