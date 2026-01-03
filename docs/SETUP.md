# Livexa Setup Guide

## Prerequisites
*   CentOS Stream 9 Server locally or on OpenShift.
*   Root access.
*   Telegram Bot Token (from @BotFather).
*   YouTube Stream Key.

## Installation
1.  **Clone Source**:
    ```bash
    git clone https://github.com/inyogeshwar/livexa-telegram-automation.git
    cd livexa-telegram-automation
    ```
2.  **Run Installer**:
    ```bash
    sudo ./install.sh
    ```
3.  **Configuration**:
    Open `/opt/livexa/config/livexa.env` and fill in:
    *   `LIVEXA_BOT_TOKEN_ENC`: Your encrypted bot token (or use `_PLAIN` for testing).
    *   `LIVEXA_ADMIN_IDS`: Your numeric Telegram ID (get it from @userinfobot).
    *   `DEFAULT_STREAM_KEY`: Your YouTube key.

## Adding Media
Place `.mp4` or `.mp3` files in:
*   `/opt/livexa/playlists/music/`
*   `/opt/livexa/playlists/gaming/`

## Start System
```bash
systemctl start livexa-bot
```
Check status:
```bash
systemctl status livexa-bot
```
