#!/bin/bash

# CONFIG
KEY="xy78-08qw-dxte-atea-3m8x"
LINK_IMAGE="https://drive.google.com/file/d/1DvwKYu5dcik1WbORt6PDGwTgdA6HDQIM/view?usp=sharing"
LINK_AUDIO="https://drive.google.com/file/d/1dIbRg8bOmu16HtDtpnyC9j4MFMqjDmyT/view?usp=drive_link"

# SETUP
mkdir -p manual_live
cd manual_live
echo "⬇️ Downloading Image..."
pip3 install gdown --upgrade &>/dev/null
gdown "$LINK_IMAGE" -O image.jpg --fuzzy

echo "⬇️ Downloading Audio..."
gdown "$LINK_AUDIO" -O audio.mp3 --fuzzy

# STREAM
echo "🚀 Starting Stream for Key: $KEY"
echo "Press Ctrl+C to Stop."

ffmpeg \
    -re \
    -loop 1 \
    -i image.jpg \
    -stream_loop -1 \
    -i audio.mp3 \
    -vf "zoompan=z='min(zoom+0.0005,1.05)':d=125" \
    -c:v libx264 \
    -preset ultrafast \
    -tune stillimage \
    -profile:v baseline \
    -level 3.0 \
    -pix_fmt yuv420p \
    -r 15 \
    -g 30 \
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
