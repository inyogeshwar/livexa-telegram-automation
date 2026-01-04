# README: LivexaBot PRO 🚀

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ━━━━━━━━━━ **L I V E X A B O T** ━━━━━━━━━━
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### **Personal Multi-Live YouTube Streaming Automation System**

**LivexaBot** is a high-reliability, Telegram-controlled automation system designed for personal creators who require multiple concurrent YouTube Live streams from a single powerful server.

---

## 🌟 Key Features
- **Multi-Live Streaming**: Run multiple independent live streams simultaneously.
- **Streaming Modes**:
    - 📹 **Video Mode**: Direct MP4 file looping.
    - 📻 **Radio Mode**: Static Image + MP3 looping.
    - 🔀 **Overlay Mode**: Video background with custom MP3 audio.
- **Auto-Quality Engine**: Supports 1080p, 720p, and 360p resolution.
- **Zero UI / Zero Code**: Control everything via Telegram commands.
- **Persistence**: Streams stay running across bot/server restarts.

---

## 🛠 One-Click Setup (CentOS / Ubuntu)

```bash
wget https://raw.githubusercontent.com/inyogeshwar/livexa-telegram-automation/main/install.sh
chmod +x install.sh
sudo ./install.sh "YOUR_BOT_TOKEN"
```

---

## 🤖 Telegram Commands

| Command | Action |
| --- | --- |
| `/newlive` | Create a new independent live session |
| `/setkey <id> <key>` | Assign YouTube stream key to a session |
| `/mode <id> video\|radio\|overlay` | Set streaming mode for the session |
| `/quality <id> <res>` | Set resolution (1080p, 720p, 360p) |
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
