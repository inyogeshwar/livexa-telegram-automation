#!/bin/bash
set -e

# INSTALLER FOR PLAYLIST BOT (Premium V2)
# Usage: sudo ./install.sh <BOT_TOKEN>

REPO_URL="https://raw.githubusercontent.com/inyogeshwar/livexa-telegram-automation/main"

if [ -z "$1" ]; then
    echo "❌ Error: Missing Bot Token."
    exit 1
fi
TOKEN="$1"

echo "🟢 Installing Playlist Bot (Premium V2)..."

# 1. Stop Service (if running)
systemctl stop livexa-bot >/dev/null 2>&1 || true

# 2. Preparation (Preserve Storage)
mkdir -p /opt/livexa/storage

# 3. Check / Download Missing Files
if [ ! -f "requirements.txt" ]; then
    echo "⬇️ Downloading requirements.txt..."
    curl -sSL "$REPO_URL/requirements.txt" -o requirements.txt
fi

if [ ! -f "bot.py" ]; then
    echo "⬇️ Downloading bot.py..."
    curl -sSL "$REPO_URL/bot.py" -o bot.py
fi

# 4. Deps
echo "📦 Installing Dependencies..."
if command -v dnf >/dev/null; then
    dnf install -y epel-release &>/dev/null
    dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm &>/dev/null
    dnf install -y python3 python3-pip ffmpeg git curl &>/dev/null
else
    apt update && apt install -y python3 python3-pip ffmpeg git curl
fi
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 5. Copy Files (Overwrite code, keep storage)
cp bot.py /opt/livexa/
cp requirements.txt /opt/livexa/

# 6. Inject Token
if [ -n "$TOKEN" ]; then
    echo "🔑 Injecting Token..."
    sed -i "s|BOT_TOKEN = \".*\"|BOT_TOKEN = \"$TOKEN\"|" /opt/livexa/bot.py
fi

# 7. Service Definition
cat <<EOF > /etc/systemd/system/livexa-bot.service
[Unit]
Description=Livexa Playlist Bot (Premium)
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

# 8. Start & Enable
systemctl daemon-reload
systemctl enable livexa-bot --now

# 9. Verify
sleep 3
if systemctl is-active --quiet livexa-bot; then
    echo "✅ SUCCESS! Premium Bot is Live."
    echo "👉 Open Telegram -> Send /start"
    echo "👉 Note: Your previous configuration (keys/files) is SAFE."
else
    echo "❌ FAILED. Logs:"
    journalctl -u livexa-bot -n 20 --no-pager
    exit 1
fi
