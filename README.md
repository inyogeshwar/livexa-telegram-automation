# Livexa - Enterprise Telegram Automation for YouTube Live

**Livexa** is a production-ready, enterprise-grade automation system that allows full control of YouTube Live streams via a Telegram Inline GUI. Built for CentOS Stream 9 on OpenShift Virtualization, it features 24/7 streaming, auto-healing FFmpeg engine, AES-256 security, and multi-VM scalability.

---

### 👤 Author & Credits
*   **Created By:** Yogeshwar Kumar
*   **GitHub:** [https://github.com/inyogeshwar](https://github.com/inyogeshwar)
*   **YouTube:** [https://www.youtube.com/@inyogeshwar_official](https://www.youtube.com/@inyogeshwar_official)
*   **Instagram:** [https://instagram.com/in_yogeshwar](https://instagram.com/in_yogeshwar)
*   **Telegram Bot:** [@LivexaBot](https://t.me/LivexaBot)

---

### 🚀 Key Features

*   **📱 Telegram Inline GUI**: Control everything with buttons (Start, Stop, Switch Playlist, Reboot). No more CLI.
*   **🔐 Enterprise Security**: AES-256 encrypted secrets. No plain text keys. Admin-locked access.
*   **🔄 Auto-Healing**: Smart watchdog restarts streams if they drop. Process deduplication.
*   **📡 Multi-Channel & Multi-Bot**: Manage unlimited channels and bots from one system.
*   **⚖️ Scalable**: Dispatcher supports multiple VMs with load balancing and failover.
*   **📂 Dynamic Playlists**: Hot-swappable music/video playlists (MP3 + MP4 mixed).

---

### 🛠 Tech Stack
*   **OS**: CentOS Stream 9 (OpenShift Virtualization compatible)
*   **Language**: Python 3.9+
*   **Framework**: `python-telegram-bot` (Async)
*   **Engine**: FFmpeg (RPM Fusion)
*   **Security**: `cryptography` (Fernet AES-256)
*   **Process Manager**: systemd

---

### 📂 Directory Structure
```
/livexa-telegram-automation
├── core/           # Bot logic, dispatcher, encryption, auth
├── engine/         # FFmpeg wrappers and watchdogs
├── config/         # Encrypted secrets and env vars
├── playlists/      # Media files (Music, Radio, Gaming)
├── systemd/        # Service definitions
├── backup/         # Snapshot & Cloud backup scripts
└── docs/           # Detailed documentation
```

### ⚡ Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/inyogeshwar/livexa-telegram-automation.git
    cd livexa-telegram-automation
    ```

2.  **Run Installer**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

3.  **Configure Secrets**
    Edit `config/livexa.env` with your Keys and IDs.

4.  **Start Services**
    ```bash
    systemctl start livexa-bot
    ```

See `docs/SETUP.md` for full installation guide.

---

**© 2026 Yogeshwar Kumar. All Rights Reserved.**
