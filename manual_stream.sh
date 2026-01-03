#!/bin/bash

# CONFIG
KEY="xy78-08qw-dxte-atea-3m8x"
LINK_VIDEO="https://drive.google.com/file/d/1DvwKYu5dcik1WbORt6PDGwTgdA6HDQIM/view?usp=sharing"
LINK_AUDIO="https://drive.google.com/file/d/1dIbRg8bOmu16HtDtpnyC9j4MFMqjDmyT/view?usp=drive_link"

# SETUP
mkdir -p manual_live
cd manual_live

echo "⬇️ Downloading VIDEO..."
pip3 install gdown --upgrade &>/dev/null
gdown "$LINK_VIDEO" -O video.mp4 --fuzzy

echo "⬇️ Downloading AUDIO..."
gdown "$LINK_AUDIO" -O audio.mp3 --fuzzy

# STREAM
echo "🚀 Starting Stream (Video + Audio)"
echo "Target: rtmp://a.rtmp.youtube.com/live2/$KEY"
echo "Press Ctrl+C to Stop."

# Loop Video (-stream_loop -1) + Loop Audio (-stream_loop -1)
# Map Video from 0, Audio from 1
# Re-encode to ensure compatibility
ffmpeg \
    -re \
    -stream_loop -1 -i video.mp4 \
    -stream_loop -1 -i audio.mp3 \
    -map 0:v \
    -map 1:a \
    -c:v libx264 \
    -preset ultrafast \
    -pix_fmt yuv420p \
    -r 25 \
    -g 50 \
    -s 426x240 \
    -b:v 300k \
    -maxrate 300k \
    -bufsize 600k \
    -c:a aac \
    -b:a 128k \
    -ac 2 \
    -ar 44100 \
    -f flv \
    "rtmp://a.rtmp.youtube.com/live2/$KEY"
