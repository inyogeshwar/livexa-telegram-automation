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
echo "📦 Installing Dependencies..."
if command -v dnf >/dev/null; then
    dnf install -y epel-release &>/dev/null
    dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm &>/dev/null
    dnf install -y python3 python3-pip ffmpeg git &>/dev/null
else
    apt update && apt install -y python3 python3-pip ffmpeg git
fi

pip3 install -r requirements.txt

# 3. Deploy Files
mkdir -p /opt/simple-bot
cp bot.py /opt/simple-bot/
cp requirements.txt /opt/simple-bot/

# 3.1 Inject Token (if provided)
if [ -n "$1" ]; then
    echo "🔑 Injecting Token: $1"
    sed -i "s|BOT_TOKEN = \".*\"|BOT_TOKEN = \"$1\"|" /opt/simple-bot/bot.py
fi

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

# 6. Verification
echo "🔍 Checking Status..."
sleep 3
if systemctl is-active --quiet simple-bot; then
    echo "--------------------------------"
    echo "✅ BOT INSTALLED & RUNNING!"
    echo "👉 If you used a new token, open that bot now."
    echo "--------------------------------"
else
    echo "❌ Bot failed to start."
    echo "📄 LOGS:"
    journalctl -u simple-bot -n 10 --no-pager
    exit 1
fi
