#!/bin/bash
# Livexa FFmpeg Engine
# Optimized for YouTube Live (RTMP)

STREAM_KEY="$1"
PLAYLIST_NAME="$2"

if [ -z "$STREAM_KEY" ] || [ -z "$PLAYLIST_NAME" ]; then
    echo "Usage: ./ffmpeg_engine.sh <STREAM_KEY> <PLAYLIST_NAME>"
    exit 1
fi

PLAYLIST_DIR="../playlists/$PLAYLIST_NAME"

if [ ! -d "$PLAYLIST_DIR" ]; then
    echo "Error: Playlist directory $PLAYLIST_DIR not found."
    exit 1
fi

# List all mp4 and mp3 files
# NOTE: In a real advanced engine, we would concat them properly or use a complex filter
# For robustness in this V1, we stream files one by one in a loop or use 'concat' demuxer
# Generating a file list for concat demuxer is safer.

LIST_FILE="/tmp/livexa_playlist_${PLAYLIST_NAME}.txt"
rm -f "$LIST_FILE"

# Populate playlist
find "$PLAYLIST_DIR" -type f \( -iname "*.mp4" -o -iname "*.mp3" \) | sort > "$LIST_FILE.tmp"
while read -r file; do
    echo "file '$file'" >> "$LIST_FILE"
done < "$LIST_FILE.tmp"
rm "$LIST_FILE.tmp"

if [ ! -s "$LIST_FILE" ]; then
    echo "Error: No media files found in $PLAYLIST_DIR"
    exit 1
fi

# Optimization Flags for YouTube
# -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3000k -bufsize 6000k
# -pix_fmt yuv420p -g 50 -c:a aac -b:a 128k -ar 44100
# -f flv rtmp://a.rtmp.youtube.com/live2/$STREAM_KEY

echo "Starting Stream for Playlist: $PLAYLIST_NAME"

ffmpeg -re -f concat -safe 0 -i "$LIST_FILE" \
    -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3000k -bufsize 6000k \
    -pix_fmt yuv420p -g 50 \
    -c:a aac -b:a 128k -ar 44100 \
    -f flv "rtmp://a.rtmp.youtube.com/live2/$STREAM_KEY"

