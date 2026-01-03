#!/bin/bash
# Livexa Watchdog
# Ensures FFmpeg runs 24/7 and restarts on failure

STREAM_KEY="$1"
PLAYLIST_NAME="$2"

if [ -z "$STREAM_KEY" ] || [ -z "$PLAYLIST_NAME" ]; then
    echo "Usage: ./ffmpeg_watchdog.sh <STREAM_KEY> <PLAYLIST_NAME>"
    exit 1
fi

echo "Starting Watchdog for $PLAYLIST_NAME..."

while true; do
    echo "Starting FFmpeg Engine..."
    # Run the engine
    bash ./ffmpeg_engine.sh "$STREAM_KEY" "$PLAYLIST_NAME"
    
    EXIT_CODE=$?
    echo "FFmpeg exited with code $EXIT_CODE"
    
    # Simple logic: If it crashes, wait 5 seconds and restart
    # If we stopped it manually (pkill), we might want to exit loop, but for now 
    # the dispatcher uses 'pkill -f ffmpeg_watchdog' to kill this wrapper too.
    
    echo "Restarting in 5 seconds..."
    sleep 5
done
