#!/bin/bash
# Livexa FFmpeg Engine V2
# Optimized for YouTube Live (RTMP)
# Supports V1 (Folder Name) and V2 (Absolute Path to List)

TARGET="$1"      # Stream Key or URL
INPUT_SRC="$2"   # Playlist Name (V1) or Absolute Path to list (V2)
MODE="$3"        # "V2" for direct list path, else V1

if [ -z "$TARGET" ] || [ -z "$INPUT_SRC" ]; then
    echo "Usage: ./ffmpeg_engine.sh <STREAM_KEY> <INPUT_SOURCE> [MODE]"
    exit 1
fi

LIST_FILE=""

if [ "$MODE" == "V2" ]; then
    # V2 Mode: INPUT_SRC is the absolute path to concat txt file
    LIST_FILE="$INPUT_SRC"
    
    if [ ! -f "$LIST_FILE" ]; then
        echo "Error: Concat file not found at $LIST_FILE"
        exit 1
    fi
else
    # V1 Mode (Legacy Support): INPUT_SRC is directory name in ../playlists/
    PLAYLIST_DIR="../playlists/$INPUT_SRC"
    if [ ! -d "$PLAYLIST_DIR" ]; then
        echo "Error: Playlist directory $PLAYLIST_DIR not found."
        exit 1
    fi
    
    LIST_FILE="/tmp/livexa_playlist_${INPUT_SRC}.txt"
    rm -f "$LIST_FILE"
    find "$PLAYLIST_DIR" -type f \( -iname "*.mp4" -o -iname "*.mp3" \) | sort > "$LIST_FILE.tmp"
    while read -r file; do
        echo "file '$file'" >> "$LIST_FILE"
    done < "$LIST_FILE.tmp"
    rm "$LIST_FILE.tmp"
fi

if [ ! -s "$LIST_FILE" ]; then
    echo "Error: Playlist file is empty."
    exit 1
fi

echo "Starting Stream..."
echo "Input: $LIST_FILE"
echo "Target: rtmp://a.rtmp.youtube.com/live2/$TARGET"

# Infinite Loop for Concat (to support looping of playlist)
# -stream_loop -1 is often better than re-executing, but for concat demuxer:
# We use -f concat -stream_loop -1 on the INPUT

ffmpeg -re -f concat -safe 0 -stream_loop -1 -i "$LIST_FILE" \
    -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3000k -bufsize 6000k \
    -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 128k -ar 44100 \
    -f flv "rtmp://a.rtmp.youtube.com/live2/$TARGET"
