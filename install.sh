#!/bin/bash
# Livexa Installer for CentOS Stream 9
# Installs FFmpeg, Python Dependencies, and sets up Systemd

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "==========================================="
echo "   Livexa Enterprise Installer"
echo "==========================================="

echo "[1/6] DNF Update & Dependencies..."
dnf update -y
dnf install -y python3 python3-pip git wget tar

echo "[2/6] Enable RPM Fusion & Install FFmpeg..."
dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm
dnf install -y ffmpeg ffmpeg-devel

echo "[3/6] Installing Python Libraries..."
pip3 install -r requirements.txt

echo "[4/6] Setting up Directories & Permissions..."
mkdir -p /opt/livexa
cp -r . /opt/livexa/
chmod +x /opt/livexa/engine/*.sh
chmod +x /opt/livexa/backup/*.sh

# Create user if not exists
if ! id "livexa" &>/dev/null; then
    useradd -r -s /bin/false livexa
fi
chown -R livexa:livexa /opt/livexa

echo "[5/6] Generating Secure Keys..."
# Generate a key if not exists
if [ ! -f /opt/livexa/config/livexa.env ]; then
    cp /opt/livexa/config/livexa.env.example /opt/livexa/config/livexa.env
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s/LIVEXA_SECRET_KEY=/LIVEXA_SECRET_KEY=$KEY/" /opt/livexa/config/livexa.env
    echo "Generated new AES-256 Key."
fi

echo "[6/6] Installing Systemd Services..."
cp systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable livexa-bot

echo "==========================================="
echo "   INSTALLATION COMPLETE"
echo "==========================================="
echo "1. Edit /opt/livexa/config/livexa.env with your Bot Token and Admin IDs."
echo "2. Upload your media to /opt/livexa/playlists/"
echo "3. Start the bot: systemctl start livexa-bot"
