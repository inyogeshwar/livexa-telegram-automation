<div align="center">

# 🔴 Livexa | Enterprise Streaming Automation
### The Telegram-Controlled YouTube Live Engine

![LivexaBot](LivexaBot.png)

[![Platform](https://img.shields.io/badge/Platform-OpenShift%20Virtualization-red?style=for-the-badge&logo=redhat)](https://www.redhat.com/en/technologies/cloud-computing/openshift/virtualization)
[![OS](https://img.shields.io/badge/OS-CentOS%20Stream%209-blue?style=for-the-badge&logo=centos)](https://www.centos.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)]()

**Author:** [Yogeshwar Kumar](https://github.com/inyogeshwar) &nbsp;|&nbsp;
**Bot:** [@LivexaBot](https://t.me/LivexaBot) &nbsp;|&nbsp;
**YouTube:** [inyogeshwar_official](https://www.youtube.com/@inyogeshwar_official) &nbsp;|&nbsp;
**Instagram:** [in_yogeshwar](https://instagram.com/in_yogeshwar)

</div>

---

## 📋 Table of Contents
- [About Livexa](#-about-livexa)
- [Why Livexa?](#-why-livexa)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Security Model](#-security-model)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Production Readiness](#-production-readiness)
- [License](#-license)

---

## 💡 About Livexa

**Livexa** is a mission-critical, enterprise-grade automation platform designed to manage 24/7 YouTube Live streams entirely via **Telegram**. 

Built for high-availablity environments on **CentOS Stream 9** and **OpenShift Virtualization**, Livexa replaces fragile CLI scripts with a robust, self-healing streaming engine controllable from your smartphone. It handles multi-channel broadcasting, dynamic playlist switching, and server management without you ever needing to SSH into a server.

---

## ❓ Why Livexa?

Traditional streaming setups are brittle. They crash, require complex OBS instances, or leave plain-text keys exposed.  
**Livexa changes the game:**

*   **📱 Zero CLI Required:** Complete control via Telegram Inline Buttons.
*   **🛡️ Military-Grade Security:** AES-256 encryption for all stream keys and tokens.
*   **⚡ Auto-Healing Engine:** Watchdog scripts detect stream drops and restart in seconds.
*   **☁️ Cloud Native:** Designed for VMs, Containers, and OpenShift clusters.

---

## 🏗 Architecture

```mermaid
graph TD
    User[📱 Admin User] -->|Telegram API| Bot[🤖 Livexa Bot Core]
    Bot -->|Auth Check| Security[🔐 Auth & Encryption Module]
    Bot -->|Dispatch| Dispatcher[🔄 Load Balancer / Dispatcher]
    
    Dispatcher -->|Start/Stop| Node1[🖥️ Node 1 (Active)]
    Dispatcher -->|Failover| Node2[🖥️ Node 2 (Standby)]
    
    Node1 -->|FFmpeg Engine| YouTube[🔴 YouTube Live Ingest]
    Node1 -->|Watchdog| Node1
    
    subgraph Storage
    Config[🔑 Encrypted Secrets]
    Media[📂 Playlist (MP4/MP3)]
    end
    
    Node1 --- Media
```

---

## 🚀 Key Features

### 🎧 **Interactive Telegram GUI**
Stop typing commands. Use modern Inline Buttons:
*   `▶ Start Live`: Select channel & playlist instantly.
*   `⏹ Stop Live`: Graceful shutdown of FFmpeg processes.
*   `🔄 Switch Playlist`: Hot-swap between Music/Gaming/Radio modes.
*   `📊 Server Stats`: Real-time CPU, RAM, and Stream Health monitoring.

### 🛡️ **Enterprise Security**
*   **AES-256 Encryption:** Your Stream Keys and Bot Tokens are never stored in plain text.
*   **Identity Locking:** Hard-coded Admin ID allowlist prevents unauthorized access.
*   **Privileged Separation:** Runs as a restricted system user, not root.

### ⚙️ **Robust Streaming Engine**
*   **FFmpeg Optimized:** tuned flags for YouTube RTMP stability (`veryfast` preset, CBR).
*   **Process Watchdog:** A dedicated background daemon monitors the stream 24/7.
*   **Smart Deduplication:** Prevents duplicate stream instances.

### 📈 **Scalability**
*   **Multi-Channel:** Support for unlimited YouTube channels.
*   **Dispatcher System:** Ready for multi-VM load balancing and failover routing.

---

## 📦 Installation

### Prerequisites
*   OS: CentOS Stream 9 (Recommended) or Ubuntu 20.04+
*   Python 3.9+
*   Root Access

### ⚡ Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/inyogeshwar/livexa-telegram-automation.git
    cd livexa-telegram-automation
    ```

2.  **Run the Enterprise Installer**
    ```bash
    chmod +x install.sh
    sudo ./install.sh
    ```
    *This script installs FFmpeg (RPM Fusion), Python dependencies, generates encryption keys, and configures systemd services.*

3.  **Verify Installation**
    ```bash
    systemctl status livexa-bot
    ```

---

## 🔧 Configuration

All sensitive configuration is handled via `config/livexa.env`.

**1. Set up Secrets**
Edit `/opt/livexa/config/livexa.env` (created during install):

```ini
# AES-256 Master Key (Auto-Generated)
LIVEXA_SECRET_KEY=...

# Your Telegram Bot Token (Encrypted or Plain for setup)
LIVEXA_BOT_TOKEN_PLAIN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Authorized Telegram User IDs (Comma Separated)
# Get yours from @userinfobot
LIVEXA_ADMIN_IDS=123456789,987654321
```

**2. Add Media**
Upload your content to the playlist folders:
*   `/opt/livexa/playlists/music/`
*   `/opt/livexa/playlists/gaming/`

---

## 📱 Usage Guide

1.  Open **@LivexaBot** in Telegram.
2.  Send command `/start`.

### 🤖 Bot Commands

#### 🔐 Admin Only
*   `/start` - Initialize the bot and show the main control panel.
*   **Control Panel** - All buttons (Start, Stop, Switch, Stats, Reboot) are restricted to Admins only.

#### 🌍 Public
*   `/about` - Show author credits and version information.

### 🎛 Control Panel (Admin)
*   **▶ Start Live:** Trigger the FFmpeg engine. By default, it plays the `music` playlist.
*   **⏹ Stop Live:** Immediately kills all stream processes.
*   **📊 Stats:** Check if the stream is healthy and view server load.
*   **♻ Reboot:** Reboot the underlying VM (Emergency Only).

---

## 🏭 Production Readiness

Livexa is designed for real-world deployment.
*   **Logs**: `journalctl -u livexa-bot -f`
*   **Backups**: Use `backup/snapshot.sh` for OpenShift VM snapshots.
*   **Cloud Sync**: Configure `backup/cloud_backup.sh` for off-site disaster recovery (Rclone).

---

## 📄 License

**© 2026 Yogeshwar Kumar.** All Rights Reserved.

This project is proprietary enterprise software released for educational and portfolio demonstration purposes.

*   **GitHub**: [inyogeshwar](https://github.com/inyogeshwar)
*   **Socials**: [YouTube](https://www.youtube.com/@inyogeshwar_official) | [Instagram](https://instagram.com/in_yogeshwar)
