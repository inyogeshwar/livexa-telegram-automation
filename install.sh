#!/bin/bash
set -e

# Livexa V3.1 Installer (Zero-CLI)

# 1. Input Validation
if [[ "$1" == "--token" && -n "$2" ]]; then
    BOT_TOKEN="$2"
else
    echo "❌ Error: Bot Token required."
    echo "Usage: sudo ./install.sh --token <YOUR_BOT_TOKEN>"
    exit 1
fi

echo "🟢 Livexa V3.1 Installer"
echo "--------------------------------"

# 2. Validate Token
echo "🔍 Validating Bot Token..."
if curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
    echo "✅ Token Valid."
else
    echo "❌ Invalid Bot Token. Please check and try again."
    exit 1
fi

# 3. System Updates & Dependencies
echo "📦 Installing Dependencies..."
if command -v dnf >/dev/null; then
    dnf install -y epel-release
    dnf install -y git python3 python3-pip ffmpeg
elif command -v apt >/dev/null; then
    apt update
    apt install -y git python3 python3-pip ffmpeg
else
    echo "❌ Unsupported OS. Use CentOS Stream 9 or Ubuntu."
    exit 1
fi

# 4. Setup Python Environment
echo "🐍 Installing Python Libs..."
pip3 install -r requirements.txt

# 5. Bootstrap Security (Encrypt Token)
echo "🔐 Encrypting Credentials..."
python3 core/bootstrap.py "$BOT_TOKEN"

# 6. Service Setup
echo "⚙️ Configuring Systemd..."
cp systemd/livexa-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable livexa-bot
systemctl start livexa-bot

echo "--------------------------------"
echo "✅ INSTALLATION COMPLETE"
echo "--------------------------------"
echo "👉 Now open Telegram and find your bot."
echo "👉 Use the /start command to claim your system."
echo "--------------------------------"
exit 0
