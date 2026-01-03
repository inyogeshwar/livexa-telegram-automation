#!/bin/bash
set -e

# INSTALLER FOR PLAYLIST BOT (User Code V4)
# Usage: sudo ./install.sh <BOT_TOKEN>

if [ -z "$1" ]; then
    echo "❌ Error: Missing Bot Token."
    exit 1
fi
TOKEN="$1"

echo "🟢 Installing Playlist Bot V4..."

# 1. Clean
systemctl stop livexa-bot >/dev/null 2>&1 || true
rm -rf /opt/livexa

# 2. Deps
echo "📦 Installing Dependencies..."
if command -v dnf >/dev/null; then
    dnf install -y epel-release &>/dev/null
    dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm &>/dev/null
    dnf install -y python3 python3-pip ffmpeg git &>/dev/null
else
    apt update && apt install -y python3 python3-pip ffmpeg git
fi
pip3 install -r requirements.txt

# 3. Setup Files
mkdir -p /opt/livexa/storage
cp bot.py /opt/livexa/
cp requirements.txt /opt/livexa/

# 3.1 Inject Token
if [ -n "$TOKEN" ]; then
    echo "🔑 Injecting Token in Code..."
    sed -i "s|BOT_TOKEN = \".*\"|BOT_TOKEN = \"$TOKEN\"|" /opt/livexa/bot.py
fi

# 4. Service
cat <<EOF > /etc/systemd/system/livexa-bot.service
[Unit]
Description=Livexa Playlist Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/livexa
ExecStart=/usr/bin/python3 bot.py
Restart=always
Environment="BOT_TOKEN=$TOKEN"

[Install]
WantedBy=multi-user.target
EOF

# 5. Start
systemctl daemon-reload
systemctl enable livexa-bot --now

# 6. Verify
sleep 3
if systemctl is-active --quiet livexa-bot; then
    echo "✅ SUCCESS! Bot is Live."
    echo "👉 Open Telegram -> Send /start"
    echo "👉 Send your Stream Key directly to bot."
else
    echo "❌ FAILED. Logs:"
    journalctl -u livexa-bot -n 20 --no-pager
    exit 1
fi
