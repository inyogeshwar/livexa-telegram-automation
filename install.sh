#!/bin/bash
set -e

# Livexa V3.1 Installer (Simpler Fallback)
# Usage: sudo ./install.sh <BOT_TOKEN> <ADMIN_ID>

# 1. INPUT VALIDATION
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "❌ Error: Missing Arguments."
    echo "Usage: sudo ./install.sh <BOT_TOKEN> <ADMIN_ID>"
    exit 1
fi
BOT_TOKEN="$1"
ADMIN_ID="$2"

echo "🟢 Livexa Installer (Manual Auth)"
echo "--------------------------------"

# 2. FAIL FAST: Validate Token
echo "🔍 Connecting to Telegram..."
if ! curl -s --max-time 10 "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
    echo "❌ CRITICAL: Invalid Bot Token or Connection Failed."
    exit 1
fi
echo "✅ Token Verified."

# 3. ENVIRONMENT SETUP
echo "📦 Installing System Components..."
if command -v dnf >/dev/null; then
    dnf install -y epel-release &>/dev/null
    # Install without gpg check for robustness in diverse repo states
    dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm &>/dev/null
    dnf install -y git python3 python3-pip ffmpeg &>/dev/null
elif command -v apt >/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y git python3 python3-pip ffmpeg -qq
else
    echo "❌ Unsupported OS."
    exit 1
fi

echo "🐍 Installing Python Dependencies..."
pip3 install -r requirements.txt --quiet --no-input

# 4. SECURE BOOTSTRAP
echo "🔐 Securing System..."
INSTALL_DIR="/opt/livexa"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

# 5. RUN BOOTSTRAP (as root, so file is root owned)
cd "$INSTALL_DIR"
python3 core/bootstrap.py "$BOT_TOKEN"

# 6. USER & PERMISSIONS (Apply chown LAST)
echo "👤 Setting Permissions..."
id -u livexa &>/dev/null || useradd -r -s /bin/false livexa
chown -R livexa:livexa "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/engine/"*.sh
# Ensure config is readable by owner (livexa) only
chmod 600 "$INSTALL_DIR/config/livexa.env"

# 7. SERVICE AUTO-START
echo "⚙️  Starting Service..."
SRV_SOURCE="$INSTALL_DIR/systemd/livexa-bot.service"
SRV_DEST="/etc/systemd/system/livexa-bot.service"
cp "$SRV_SOURCE" "$SRV_DEST"

systemctl daemon-reload
systemctl enable livexa-bot --now

# 8. VERIFICATION
echo "🔍 Verifying Service..."
if systemctl is-active --quiet livexa-bot; then
    echo "✅ Service is RUNNING."
else
    echo "❌ Service FAILED to start."
    echo "👉 Check logs: journalctl -u livexa-bot -n 20"
    exit 1
fi

echo "--------------------------------"
echo "✅ INSTALL SUCCESSFUL"
echo "--------------------------------"
echo "👉 Open Telegram now."
echo "👉 Reply 'YES' to claim this bot."
echo "--------------------------------"
exit 0
