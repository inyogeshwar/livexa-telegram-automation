#!/bin/bash
set -e

# INSTALLATION for Simple Bot
# Usage: sudo ./install.sh

if [ "$(id -u)" != "0" ]; then
    echo "❌ Please run as sudo (root)"
    exit 1
fi

echo "🟢 Installing Simple Bot..."

# 1. Clean old install
rm -rf /opt/simple-bot
systemctl stop livexa-bot >/dev/null 2>&1 || true
systemctl disable livexa-bot >/dev/null 2>&1 || true
rm -f /etc/systemd/system/livexa-bot.service

# 2. Dependencies
if command -v dnf >/dev/null; then
    dnf install -y python3 python3-pip ffmpeg git
else
    apt update && apt install -y python3 python3-pip ffmpeg git
fi

pip3 install -r requirements.txt

# 3. Deploy Files
mkdir -p /opt/simple-bot
cp bot.py /opt/simple-bot/
cp requirements.txt /opt/simple-bot/

# 4. Create Service
cat <<EOF > /etc/systemd/system/simple-bot.service
[Unit]
Description=Simple Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/simple-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Start
systemctl daemon-reload
systemctl enable simple-bot --now

echo "--------------------------------"
echo "✅ BOT INSTALLED & RUNNING!"
echo "👉 Telegram: @LivexaBot (Check if it works)"
echo "--------------------------------"
